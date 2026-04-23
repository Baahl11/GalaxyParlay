"use client";

// Marc Loyera Picks — Neon Board
import type { ValueBet } from "@/lib/api";
import { getModelPicks, getStats, getValueBets } from "@/lib/api";
import type { StatsResponse } from "@/lib/types";
import { useEffect, useMemo, useState } from "react";

const MARKET_LABELS: Record<string, string> = {
  match_winner: "Ganador",
  over_under_2_5: "Over/Under 2.5",
  both_teams_score: "BTTS",
};

function toAmericanOdds(decimalOdds: number): string {
  if (!decimalOdds || decimalOdds <= 1) return "—";
  const profit = decimalOdds - 1;
  if (profit >= 1) return `+${Math.round(profit * 100)}`;
  return `-${Math.round(100 / profit)}`;
}

function scorePick(bet: ValueBet): number {
  const gradeWeight: Record<string, number> = {
    A: 1,
    B: 0.85,
    C: 0.7,
    D: 0.55,
    F: 0.4,
  };
  const weight = gradeWeight[bet.grade] ?? 0.6;
  const confScore = (bet.confidence || 0) * 60 * weight;
  const evScore = bet.odds_source === "bookmaker" ? bet.ev * 140 * weight : 0;
  const edgeScore =
    bet.odds_source === "bookmaker" ? bet.edge * 100 * weight : 0;
  return confScore + evScore + edgeScore;
}

function isSameLocalDay(date: Date, base: Date): boolean {
  if (Number.isNaN(date.getTime())) return false;
  return (
    date.getFullYear() === base.getFullYear() &&
    date.getMonth() === base.getMonth() &&
    date.getDate() === base.getDate()
  );
}

export default function Home() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [picks, setPicks] = useState<ValueBet[]>([]);
  const [picksSource, setPicksSource] = useState<"value" | "model" | "mixed">(
    "value",
  );
  const [viewMode, setViewMode] = useState<"quality" | "volume">("volume");
  const [timeScope, setTimeScope] = useState<"today" | "all">("today");
  const [gradeFilter, setGradeFilter] = useState<
    "all" | "A" | "B" | "C" | "D"
  >("all");
  const [showCount, setShowCount] = useState<number>(30);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    const fetchLimit = Math.max(showCount * 2, timeScope === "all" ? 600 : 60);
    const valueParams =
      viewMode === "quality"
        ? { limit: fetchLimit, min_edge: 0.03, min_ev: 0.02 }
        : { limit: fetchLimit, min_edge: 0, min_ev: 0 };
    let modelParams: Parameters<typeof getModelPicks>[0] =
      viewMode === "quality"
        ? { limit: fetchLimit, min_confidence: 0.6, grades: ["A", "B"] }
        : {
            limit: fetchLimit,
            min_confidence: 0.45,
            grades: ["A", "B", "C", "D"],
          };
    if (gradeFilter === "A") {
      modelParams = { ...modelParams, min_confidence: 0, grades: ["A"] };
    }
    if (timeScope === "all") {
      modelParams = { ...modelParams, status: "ALL" };
    }

    Promise.all([getStats(), getValueBets(valueParams)])
      .then(async ([statsData, valueData]) => {
        setStats(statsData);
        const valueBets = valueData.bets;
        const now = new Date();
        const scopeIsToday = timeScope === "today";
        const valueBetsScoped = scopeIsToday
          ? valueBets.filter((bet) =>
              isSameLocalDay(new Date(bet.kickoff_time), now),
            )
          : valueBets;
        let modelPicks: ValueBet[] = [];
        const needsModel =
          valueBetsScoped.length < showCount || viewMode === "volume";
        if (needsModel) {
          modelPicks = await getModelPicks(modelParams);
        }
        const valueKeys = new Set(
          valueBetsScoped.map((b) => `${b.fixture_id}-${b.market}`),
        );
        const modelPicksScoped = scopeIsToday
          ? modelPicks.filter((bet) =>
              isSameLocalDay(new Date(bet.kickoff_time), now),
            )
          : modelPicks;
        const dedupedModel = modelPicksScoped.filter(
          (b) => !valueKeys.has(`${b.fixture_id}-${b.market}`),
        );
        const merged = [...valueBetsScoped, ...dedupedModel];
        setPicks(merged);
        if (valueBetsScoped.length > 0 && dedupedModel.length > 0) {
          setPicksSource("mixed");
        } else if (valueBetsScoped.length > 0) {
          setPicksSource("value");
        } else {
          setPicksSource("model");
        }
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Error cargando picks");
      })
      .finally(() => setLoading(false));
  }, [showCount, viewMode, timeScope, gradeFilter]);

  const filteredPicks = useMemo(() => {
    if (gradeFilter === "all") return picks;
    return picks.filter((bet) => bet.grade === gradeFilter);
  }, [picks, gradeFilter]);

  const rankedPicks = useMemo(() => {
    return [...filteredPicks]
      .sort((a, b) => scorePick(b) - scorePick(a))
      .slice(0, showCount);
  }, [filteredPicks, showCount]);

  const gradeAInScope = useMemo(() => {
    return picks.filter((bet) => bet.grade === "A").length;
  }, [picks]);

  const todayLabel = new Date().toLocaleDateString("es-ES", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });

  return (
    <div className="neon-bg text-white">
      <div className="max-w-6xl mx-auto px-4 py-8">
        <header className="neon-panel rounded-3xl p-6 md:p-8 mb-6">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="neon-outline rounded-2xl px-4 py-3 text-xl font-display">
                ML
              </div>
              <div>
                <p className="text-sm uppercase tracking-[0.35em] text-cyan-300 font-display">
                  Marc Loyera
                </p>
                <h1 className="text-4xl md:text-5xl font-display neon-title">
                  PICKS
                </h1>
                <p className="text-xs text-gray-400 tracking-[0.3em] mt-2">
                  SMART BETTING ONLY
                </p>
              </div>
            </div>
            <div className="flex flex-wrap gap-3">
              <div className="neon-chip rounded-xl px-4 py-2 text-xs uppercase tracking-[0.2em]">
                <span className="block text-[10px] text-cyan-300">Fecha</span>
                <span className="text-white font-semibold">{todayLabel}</span>
              </div>
              <div className="neon-chip rounded-xl px-4 py-2 text-xs uppercase tracking-[0.2em]">
                <span className="block text-[10px] text-cyan-300">Gestión</span>
                <span className="text-white font-semibold">1-3% por pick</span>
              </div>
              <div className="neon-chip rounded-xl px-4 py-2 text-xs uppercase tracking-[0.2em]">
                <span className="block text-[10px] text-cyan-300">Fuente</span>
                <span className="text-white font-semibold">
                  {picksSource === "value"
                    ? "Odds reales"
                    : picksSource === "mixed"
                      ? "Mixto"
                      : "Cuota modelo"}
                </span>
              </div>
            </div>
          </div>
        </header>

        <section className="neon-panel rounded-3xl p-6 md:p-8 mb-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h2 className="text-lg font-display tracking-wider text-white">
                {timeScope === "today"
                  ? "Ranking de Picks del Día"
                  : "Ranking de Picks Globales"}
              </h2>
              <p className="text-sm text-gray-400">
                Ordenados por EV, edge y confianza del modelo.
              </p>
            </div>
            <div className="flex gap-3 flex-wrap text-xs">
              <span className="px-3 py-1 rounded-full neon-chip text-cyan-200">
                {rankedPicks.length} / {filteredPicks.length} picks
              </span>
              <span className="px-3 py-1 rounded-full neon-chip text-cyan-200">
                {gradeAInScope} grado A
                {timeScope === "today" ? " hoy" : " en vista"}
              </span>
              {stats && (
                <button
                  type="button"
                  onClick={() => {
                    setTimeScope("all");
                    setGradeFilter("A");
                    setViewMode("quality");
                    setShowCount(400);
                  }}
                  className="px-3 py-1 rounded-full neon-chip text-cyan-200 hover:text-white hover:border-cyan-200/60 transition-colors"
                >
                  {stats.predictions?.grade_a ?? 0} grado A global
                </button>
              )}
            </div>
          </div>

          <div className="mt-4 flex flex-wrap gap-3 text-xs">
            <div className="flex items-center gap-2">
              <span className="text-cyan-300 uppercase tracking-[0.2em]">
                Alcance
              </span>
              {(
                [
                  { key: "today", label: "Hoy" },
                  { key: "all", label: "Todos" },
                ] as const
              ).map((scope) => (
                <button
                  key={scope.key}
                  onClick={() => setTimeScope(scope.key)}
                  className={`px-3 py-1 rounded-full transition-colors ${
                    timeScope === scope.key
                      ? "bg-emerald-500/30 text-emerald-100 border border-emerald-400/40"
                      : "bg-gray-900/50 text-gray-400 border border-gray-700/50"
                  }`}
                >
                  {scope.label}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-cyan-300 uppercase tracking-[0.2em]">
                Modo
              </span>
              {(
                [
                  { key: "quality", label: "Calidad" },
                  { key: "volume", label: "Volumen" },
                ] as const
              ).map((mode) => (
                <button
                  key={mode.key}
                  onClick={() => setViewMode(mode.key)}
                  className={`px-3 py-1 rounded-full transition-colors ${
                    viewMode === mode.key
                      ? "bg-cyan-500/30 text-cyan-100 border border-cyan-400/40"
                      : "bg-gray-900/50 text-gray-400 border border-gray-700/50"
                  }`}
                >
                  {mode.label}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-cyan-300 uppercase tracking-[0.2em]">
                Grado
              </span>
              {(
                ["all", "A", "B", "C", "D"] as const
              ).map((grade) => (
                <button
                  key={grade}
                  onClick={() => setGradeFilter(grade)}
                  className={`px-3 py-1 rounded-full transition-colors ${
                    gradeFilter === grade
                      ? "bg-indigo-500/30 text-indigo-100 border border-indigo-400/40"
                      : "bg-gray-900/50 text-gray-400 border border-gray-700/50"
                  }`}
                >
                  {grade === "all" ? "Todos" : grade}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-cyan-300 uppercase tracking-[0.2em]">
                Mostrar
              </span>
              {[12, 30, 60, 120, 200, 300, 400].map((count) => (
                <button
                  key={count}
                  onClick={() => setShowCount(count)}
                  className={`px-3 py-1 rounded-full transition-colors ${
                    showCount === count
                      ? "bg-purple-500/30 text-purple-100 border border-purple-400/40"
                      : "bg-gray-900/50 text-gray-400 border border-gray-700/50"
                  }`}
                >
                  {count}
                </button>
              ))}
            </div>
          </div>

          {loading && (
            <div className="mt-6 space-y-3">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-16 rounded-2xl neon-row opacity-60" />
              ))}
            </div>
          )}

          {!loading && error && (
            <div className="mt-6 rounded-2xl bg-red-900/30 border border-red-500/40 p-4 text-sm text-red-200">
              {error}
            </div>
          )}

          {!loading && !error && rankedPicks.length === 0 && (
            <div className="mt-6 rounded-2xl neon-row p-6 text-center text-sm text-gray-300">
              No hay picks disponibles hoy. Las predicciones se actualizan cada
              6 horas.
            </div>
          )}

          {!loading && !error && rankedPicks.length > 0 && (
            <div className="mt-6 space-y-3">
              <div className="hidden md:grid grid-cols-[70px_1.6fr_1.2fr_120px_120px] text-xs uppercase tracking-[0.3em] text-cyan-200">
                <span>#</span>
                <span>Partido</span>
                <span>Pick</span>
                <span>Cuota</span>
                <span>Prob.</span>
              </div>
              {rankedPicks.map((bet, index) => {
                const probability = Math.round(bet.model_prob * 100);
                return (
                  <div
                    key={`${bet.fixture_id}-${bet.market}`}
                    className="neon-row rounded-2xl px-4 py-3"
                  >
                    <div className="grid gap-4 md:grid-cols-[70px_1.6fr_1.2fr_120px_120px] items-center">
                      <div className="flex items-center gap-3">
                        <span className="neon-outline rounded-lg px-3 py-1 text-sm font-display">
                          {String(index + 1).padStart(2, "0")}
                        </span>
                      </div>

                      <div>
                        <p className="font-semibold text-white">
                          {bet.home_team}{" "}
                          <span className="text-gray-500">vs</span>{" "}
                          {bet.away_team}
                        </p>
                        <p className="text-xs text-gray-400">
                          {MARKET_LABELS[bet.market] ?? bet.market} ·{" "}
                          {new Date(bet.kickoff_time).toLocaleString("es-ES", {
                            weekday: "short",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </p>
                      </div>

                      <div className="flex flex-wrap gap-2">
                        <span className="px-2 py-1 rounded-full text-xs bg-cyan-500/20 text-cyan-200 border border-cyan-400/30">
                          {bet.selection}
                        </span>
                        <span className="px-2 py-1 rounded-full text-xs bg-purple-500/20 text-purple-200 border border-purple-400/30">
                          Grado {bet.grade}
                        </span>
                        <span className="px-2 py-1 rounded-full text-xs bg-emerald-500/20 text-emerald-200 border border-emerald-400/30">
                          Conf. {Math.round(bet.confidence * 100)}%
                        </span>
                      </div>

                      <div className="text-sm font-semibold text-yellow-200">
                        {toAmericanOdds(bet.odds)}
                        <span className="ml-2 text-xs text-gray-400">
                          @{bet.odds.toFixed(2)}
                        </span>
                      </div>

                      <div className="flex items-center gap-3">
                        <div className="neon-ring">{probability}%</div>
                        <div className="text-xs text-gray-400">
                          {bet.odds_source === "model"
                            ? "Cuota modelo"
                            : "Odds reales"}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          <div className="neon-panel rounded-2xl p-5">
            <h3 className="text-sm uppercase tracking-[0.3em] text-cyan-200">
              Record del Modelo
            </h3>
            <p className="mt-2 text-2xl font-display text-white">
              {stats?.predictions?.total ?? 0} predicciones
            </p>
            <p className="text-xs text-gray-400">
              {stats?.predictions?.grade_a ?? 0} grado A · actualizado hoy
            </p>
          </div>
          <div className="neon-panel rounded-2xl p-5">
            <h3 className="text-sm uppercase tracking-[0.3em] text-cyan-200">
              Disciplina
            </h3>
            <p className="mt-2 text-xl font-display text-white">
              Confianza · Constancia
            </p>
            <p className="text-xs text-gray-400">
              Juega con responsabilidad · +18
            </p>
          </div>
          <div className="neon-panel rounded-2xl p-5">
            <h3 className="text-sm uppercase tracking-[0.3em] text-cyan-200">
              Contacto
            </h3>
            <p className="mt-2 text-sm text-gray-300">@marcloyera.picks</p>
            <p className="text-xs text-gray-400">Instagram · Telegram</p>
          </div>
        </section>
      </div>
    </div>
  );
}
