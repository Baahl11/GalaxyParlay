"use client";

import { getModelPicks, getValueBets, type ValueBet } from "@/lib/api";
import { useEffect, useState } from "react";
import { PickCard } from "./PickCard";

interface TodayPicksProps {
  parlayPicks: ValueBet[];
  highlightedFixtureId?: number | null;
  onToggleParlay: (bet: ValueBet) => void;
  onClickFixture?: (fixtureId: number) => void;
  onPicksLoaded?: (bets: ValueBet[]) => void;
}

type SortKey = "ev" | "odds" | "confidence";

export function TodayPicks({
  parlayPicks,
  highlightedFixtureId,
  onToggleParlay,
  onClickFixture,
  onPicksLoaded,
}: TodayPicksProps) {
  const [bets, setBets] = useState<ValueBet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<SortKey>("ev");
  const [gradeFilter, setGradeFilter] = useState<string>("all");
  const [picksSource, setPicksSource] = useState<"value" | "model">("value");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getValueBets({ limit: 50 })
      .then(async ({ bets: data }) => {
        if (cancelled) return;
        if (data.length > 0) {
          setBets(data);
          setPicksSource("value");
          onPicksLoaded?.(data);
          return;
        }
        const modelPicks = await getModelPicks({ limit: 50 });
        if (cancelled) return;
        setBets(modelPicks);
        setPicksSource("model");
        setSortBy("confidence");
        onPicksLoaded?.(modelPicks);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Error cargando picks");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [onPicksLoaded]);

  const parlaySet = new Set(
    parlayPicks.map((p) => `${p.fixture_id}-${p.market}`),
  );

  const sorted = [...bets]
    .filter((b) => gradeFilter === "all" || b.grade === gradeFilter)
    .sort((a, b) => {
      if (sortBy === "ev") return b.ev - a.ev;
      if (sortBy === "odds") return b.odds - a.odds;
      return b.confidence - a.confidence;
    });

  const grades = [
    "all",
    ...Array.from(new Set(bets.map((b) => b.grade))).sort(),
  ];

  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            className="h-36 bg-gray-800/40 rounded-xl border border-gray-700/30 animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl bg-red-900/20 border border-red-500/30 p-6 text-center">
        <p className="text-red-400 text-sm mb-3">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="text-xs text-red-300 hover:text-white underline"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (sorted.length === 0) {
    return (
      <div className="rounded-xl bg-gray-800/30 border border-gray-700/30 p-8 text-center">
        <div className="text-4xl mb-3">🔭</div>
        <p className="text-gray-400 text-sm">No hay picks disponibles hoy.</p>
        <p className="text-gray-600 text-xs mt-1">
          Las predicciones se actualizan cada 6 horas.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {picksSource === "model" && (
        <div className="mb-3 rounded-lg border border-purple-500/30 bg-purple-500/10 px-3 py-2 text-xs text-purple-200">
          Sin odds reales por ahora. Mostrando picks del modelo con cuota justa.
        </div>
      )}
      {/* Controls */}
      <div className="flex items-center gap-2 mb-3 flex-wrap">
        {/* Grade filter pills */}
        <div className="flex gap-1 flex-wrap">
          {grades.map((g) => (
            <button
              key={g}
              onClick={() => setGradeFilter(g)}
              className={`px-2.5 py-1 rounded-full text-xs font-semibold transition-colors ${
                gradeFilter === g
                  ? "bg-purple-600 text-white"
                  : "bg-gray-700/60 text-gray-400 hover:bg-gray-600/60"
              }`}
            >
              {g === "all" ? "Todos" : `Grado ${g}`}
            </button>
          ))}
        </div>

        {/* Sort selector */}
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as SortKey)}
          className="ml-auto text-xs bg-gray-700/60 border border-gray-600/40 text-gray-300 rounded-lg px-2 py-1 focus:outline-none focus:ring-1 focus:ring-purple-500"
        >
          <option value="ev">EV más alto</option>
          <option value="odds">Cuota más alta</option>
          <option value="confidence">Confianza</option>
        </select>
      </div>

      {/* Count */}
      <p className="text-xs text-gray-500 mb-3">
        {sorted.length} pick{sorted.length !== 1 ? "s" : ""} disponible
        {sorted.length !== 1 ? "s" : ""}
      </p>

      {/* Cards */}
      <div className="space-y-3 overflow-y-auto flex-1 pr-1">
        {sorted.map((bet) => (
          <PickCard
            key={`${bet.fixture_id}-${bet.market}`}
            bet={bet}
            inParlay={parlaySet.has(`${bet.fixture_id}-${bet.market}`)}
            highlighted={highlightedFixtureId === bet.fixture_id}
            onToggleParlay={onToggleParlay}
            onClickFixture={onClickFixture}
          />
        ))}
      </div>
    </div>
  );
}
