"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { supabase } from "@/lib/supabase";
import { LEAGUE_FLAGS, LEAGUE_NAMES } from "@/lib/types";

interface HistorialRow {
  fixture_id: number;
  home_team: string;
  away_team: string;
  kickoff_time: string;
  league_id: number;
  market_key: string;
  selection: string;
  model_prob: number;
  grade: string;
  confidence: number;
  actual_home: number | null;
  actual_away: number | null;
  status: string;
  outcome: "correct" | "wrong" | "pending";
}

const MARKET_LABELS: Record<string, string> = {
  match_winner: "1X2",
  over_under_2_5: "O/U 2.5",
  both_teams_score: "BTTS",
};

function determineOutcome(
  market: string,
  selection: string,
  homeGoals: number,
  awayGoals: number,
): "correct" | "wrong" {
  const total = homeGoals + awayGoals;

  if (market === "match_winner") {
    const actual =
      homeGoals > awayGoals ? "Home Win" : homeGoals < awayGoals ? "Away Win" : "Draw";
    return actual === selection ? "correct" : "wrong";
  }
  if (market === "over_under_2_5") {
    if (selection === "Over 2.5") return total > 2.5 ? "correct" : "wrong";
    if (selection === "Under 2.5") return total < 2.5 ? "correct" : "wrong";
  }
  if (market === "both_teams_score") {
    const btts = homeGoals > 0 && awayGoals > 0;
    if (selection === "BTTS Yes") return btts ? "correct" : "wrong";
    if (selection === "BTTS No") return !btts ? "correct" : "wrong";
  }
  return "wrong";
}

function deriveSelection(market: string, pred: Record<string, number>): string {
  if (market === "match_winner") {
    const best = Math.max(pred.home_win ?? 0, pred.draw ?? 0, pred.away_win ?? 0);
    if (best === (pred.home_win ?? 0)) return "Home Win";
    if (best === (pred.draw ?? 0)) return "Draw";
    return "Away Win";
  }
  if (market === "over_under_2_5") {
    return (pred.over ?? 0) >= (pred.under ?? 0) ? "Over 2.5" : "Under 2.5";
  }
  if (market === "both_teams_score") {
    return (pred.yes ?? 0) >= (pred.no ?? 0) ? "BTTS Yes" : "BTTS No";
  }
  return "";
}

export default function HistorialPage() {
  const [rows, setRows] = useState<HistorialRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [gradeFilter, setGradeFilter] = useState<"all" | "S" | "A" | "B" | "C">("all");
  const [marketFilter, setMarketFilter] = useState<"all" | "match_winner" | "over_under_2_5" | "both_teams_score">("all");
  const [page, setPage] = useState(0);
  const PAGE_SIZE = 50;

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        // Fetch completed fixtures with predictions for key markets
        const { data, error: err } = await supabase
          .from("model_predictions")
          .select(
            `market_key, prediction, confidence_score, quality_grade, fixture_id,
             fixtures!inner(home_team_name, away_team_name, kickoff_time, league_id, status, home_score, away_score)`,
          )
          .in("market_key", ["match_winner", "over_under_2_5", "both_teams_score"])
          .gte("confidence_score", 0.5)
          .in("quality_grade", ["S", "A", "B", "C"])
          .order("fixture_id", { ascending: false })
          .limit(2000);

        if (err) throw new Error(err.message);

        const built: HistorialRow[] = [];
        for (const row of data ?? []) {
          const fx = row.fixtures as unknown as {
            home_team_name: string;
            away_team_name: string;
            kickoff_time: string;
            league_id: number;
            status: string;
            home_score: number | null;
            away_score: number | null;
          };

          const isFinished = ["FT", "AET", "PEN"].includes(fx.status);
          const pred = row.prediction as Record<string, number>;
          const selection = deriveSelection(row.market_key as string, pred);
          if (!selection) continue;

          const homeGoals = fx.home_score ?? null;
          const awayGoals = fx.away_score ?? null;

          let outcome: "correct" | "wrong" | "pending" = "pending";
          if (isFinished && homeGoals !== null && awayGoals !== null) {
            outcome = determineOutcome(
              row.market_key as string,
              selection,
              homeGoals,
              awayGoals,
            );
          }

          built.push({
            fixture_id: row.fixture_id as number,
            home_team: fx.home_team_name,
            away_team: fx.away_team_name,
            kickoff_time: fx.kickoff_time,
            league_id: fx.league_id,
            market_key: row.market_key as string,
            selection,
            model_prob: Math.round((row.confidence_score as number) * 1000) / 1000,
            grade: row.quality_grade as string,
            confidence: Math.round((row.confidence_score as number) * 1000) / 1000,
            actual_home: homeGoals,
            actual_away: awayGoals,
            status: fx.status,
            outcome,
          });
        }

        // Dedup by fixture_id + market_key (keep highest confidence)
        const dedupMap = new Map<string, HistorialRow>();
        for (const r of built) {
          const k = `${r.fixture_id}-${r.market_key}`;
          const existing = dedupMap.get(k);
          if (!existing || r.confidence > existing.confidence) dedupMap.set(k, r);
        }

        const final = Array.from(dedupMap.values()).sort(
          (a, b) => new Date(b.kickoff_time).getTime() - new Date(a.kickoff_time).getTime(),
        );

        setRows(final);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Error cargando historial");
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  const filtered = useMemo(() => {
    let r = rows;
    if (gradeFilter !== "all") r = r.filter((x) => x.grade === gradeFilter);
    if (marketFilter !== "all") r = r.filter((x) => x.market_key === marketFilter);
    return r;
  }, [rows, gradeFilter, marketFilter]);

  const paginated = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  const stats = useMemo(() => {
    const decided = filtered.filter((r) => r.outcome !== "pending");
    const correct = decided.filter((r) => r.outcome === "correct").length;
    const accuracy = decided.length > 0 ? Math.round((correct / decided.length) * 1000) / 10 : null;
    const gradeA = decided.filter((r) => (r.grade === "A" || r.grade === "S") && r.outcome === "correct").length;
    const gradeATotal = decided.filter((r) => r.grade === "A" || r.grade === "S").length;
    const gradeAAccuracy = gradeATotal > 0 ? Math.round((gradeA / gradeATotal) * 1000) / 10 : null;
    return { decided: decided.length, correct, accuracy, gradeAAccuracy, total: filtered.length };
  }, [filtered]);

  return (
    <div className="neon-bg text-white min-h-screen">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <header className="neon-panel rounded-3xl p-6 mb-6">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-cyan-300">Marc Loyera</p>
              <h1 className="text-4xl font-display neon-title">HISTORIAL</h1>
              <p className="text-xs text-gray-400 mt-1">Picks pasados con resultados verificables · 18+</p>
            </div>
            <div className="flex flex-wrap gap-3">
              {stats.accuracy !== null && (
                <div className="neon-chip rounded-xl px-4 py-2 text-xs">
                  <span className="block text-[10px] text-cyan-300">Accuracy global</span>
                  <span className="text-white font-semibold text-sm">{stats.accuracy}%</span>
                  <span className="text-gray-400 ml-1">({stats.correct}/{stats.decided})</span>
                </div>
              )}
              {stats.gradeAAccuracy !== null && (
                <div className="neon-chip rounded-xl px-4 py-2 text-xs">
                  <span className="block text-[10px] text-cyan-300">Grado A/S</span>
                  <span className="text-white font-semibold text-sm">{stats.gradeAAccuracy}%</span>
                </div>
              )}
              <div className="neon-chip rounded-xl px-4 py-2 text-xs">
                <span className="block text-[10px] text-cyan-300">Total picks</span>
                <span className="text-white font-semibold text-sm">{stats.total}</span>
              </div>
              <Link
                href="/"
                className="px-4 py-2 rounded-full border border-cyan-400/40 text-cyan-200 text-xs hover:bg-cyan-500/20 self-center"
              >
                ← Picks
              </Link>
            </div>
          </div>
        </header>

        {/* Filters */}
        <div className="neon-panel rounded-2xl p-4 mb-6 flex flex-wrap gap-4 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-cyan-300 uppercase tracking-[0.2em]">Grado</span>
            {(["all", "S", "A", "B", "C"] as const).map((g) => (
              <button
                key={g}
                onClick={() => { setGradeFilter(g); setPage(0); }}
                className={`px-3 py-1 rounded-full transition-colors ${
                  gradeFilter === g
                    ? "bg-indigo-500/30 text-indigo-100 border border-indigo-400/40"
                    : "bg-gray-900/50 text-gray-400 border border-gray-700/50"
                }`}
              >
                {g === "all" ? "Todos" : g}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-cyan-300 uppercase tracking-[0.2em]">Mercado</span>
            {(["all", "match_winner", "over_under_2_5", "both_teams_score"] as const).map((m) => (
              <button
                key={m}
                onClick={() => { setMarketFilter(m); setPage(0); }}
                className={`px-3 py-1 rounded-full transition-colors ${
                  marketFilter === m
                    ? "bg-cyan-500/30 text-cyan-100 border border-cyan-400/40"
                    : "bg-gray-900/50 text-gray-400 border border-gray-700/50"
                }`}
              >
                {m === "all" ? "Todos" : MARKET_LABELS[m] ?? m}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <div className="neon-panel rounded-2xl overflow-hidden">
          {loading && (
            <div className="p-8 space-y-3">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="h-12 rounded-xl neon-row opacity-50" />
              ))}
            </div>
          )}

          {!loading && error && (
            <div className="p-6 text-red-300 text-sm">{error}</div>
          )}

          {!loading && !error && filtered.length === 0 && (
            <div className="p-8 text-center text-gray-400 text-sm">
              No hay historial disponible aún. Los resultados se actualizan cada 3h.
            </div>
          )}

          {!loading && !error && filtered.length > 0 && (
            <>
              {/* Header row */}
              <div className="hidden md:grid grid-cols-[1.5fr_1.2fr_100px_90px_80px_80px_80px] gap-3 px-4 py-3 text-xs uppercase tracking-[0.25em] text-cyan-300 border-b border-gray-800">
                <span>Partido</span>
                <span>Pick</span>
                <span>Mercado</span>
                <span>Prob.</span>
                <span>Grado</span>
                <span>Score</span>
                <span>Resultado</span>
              </div>

              {paginated.map((row) => {
                const flag = LEAGUE_FLAGS[row.league_id] ?? "⚽";
                const leagueName = LEAGUE_NAMES[row.league_id] ?? `Liga ${row.league_id}`;
                const kickoff = new Date(row.kickoff_time);
                const dateStr = kickoff.toLocaleDateString("es-ES", { day: "2-digit", month: "short", year: "numeric" });

                return (
                  <div
                    key={`${row.fixture_id}-${row.market_key}`}
                    className="grid md:grid-cols-[1.5fr_1.2fr_100px_90px_80px_80px_80px] gap-3 px-4 py-3 border-b border-gray-800/60 hover:bg-white/[0.02] items-center"
                  >
                    <div>
                      <p className="text-sm text-white font-medium">
                        {row.home_team} <span className="text-gray-500">vs</span> {row.away_team}
                      </p>
                      <p className="text-xs text-gray-500">
                        {flag} {leagueName} · {dateStr}
                      </p>
                    </div>

                    <div>
                      <span className="px-2 py-1 rounded-full text-xs bg-cyan-500/20 text-cyan-200 border border-cyan-400/30">
                        {row.selection}
                      </span>
                    </div>

                    <div className="text-xs text-gray-400">
                      {MARKET_LABELS[row.market_key] ?? row.market_key}
                    </div>

                    <div className="text-sm font-semibold text-white">
                      {Math.round(row.model_prob * 100)}%
                    </div>

                    <div>
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-bold ${
                          row.grade === "S" || row.grade === "A"
                            ? "bg-green-500/20 text-green-300 border border-green-500/30"
                            : row.grade === "B"
                            ? "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                            : "bg-yellow-500/20 text-yellow-300 border border-yellow-500/30"
                        }`}
                      >
                        {row.grade}
                      </span>
                    </div>

                    <div className="text-sm text-gray-300">
                      {row.actual_home !== null && row.actual_away !== null
                        ? `${row.actual_home} - ${row.actual_away}`
                        : "—"}
                    </div>

                    <div>
                      {row.outcome === "correct" && (
                        <span className="text-emerald-400 font-bold text-sm">✓ Correcto</span>
                      )}
                      {row.outcome === "wrong" && (
                        <span className="text-red-400 font-bold text-sm">✗ Error</span>
                      )}
                      {row.outcome === "pending" && (
                        <span className="text-gray-500 text-xs">Pendiente</span>
                      )}
                    </div>
                  </div>
                );
              })}

              {/* Pagination */}
              {filtered.length > PAGE_SIZE && (
                <div className="p-4 flex justify-center gap-3">
                  <button
                    onClick={() => setPage((p) => Math.max(0, p - 1))}
                    disabled={page === 0}
                    className="px-4 py-2 rounded-full text-xs border border-gray-700 text-gray-400 disabled:opacity-40 hover:border-cyan-500/50"
                  >
                    ← Anterior
                  </button>
                  <span className="text-xs text-gray-500 self-center">
                    Pág. {page + 1} / {Math.ceil(filtered.length / PAGE_SIZE)}
                  </span>
                  <button
                    onClick={() => setPage((p) => Math.min(Math.ceil(filtered.length / PAGE_SIZE) - 1, p + 1))}
                    disabled={page >= Math.ceil(filtered.length / PAGE_SIZE) - 1}
                    className="px-4 py-2 rounded-full text-xs border border-gray-700 text-gray-400 disabled:opacity-40 hover:border-cyan-500/50"
                  >
                    Siguiente →
                  </button>
                </div>
              )}
            </>
          )}
        </div>

        <p className="mt-4 text-center text-xs text-gray-600">
          Solo con fines educativos · 18+ · Los resultados pasados no garantizan resultados futuros
        </p>
      </div>
    </div>
  );
}
