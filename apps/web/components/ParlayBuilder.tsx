"use client";

import type { ValueBet } from "@/lib/api";
import { LEAGUE_FLAGS } from "@/lib/types";
import { useCallback } from "react";

interface ParlayBuilderProps {
  picks: ValueBet[];
  onRemovePick: (fixtureId: number, market: string) => void;
  onClear: () => void;
}

function buildShareText(picks: ValueBet[], combinedOdds: number): string {
  const lines = [
    "🎲 Mi Parlay — GalaxyParlay",
    "",
    ...picks.map((p) => {
      const flag = LEAGUE_FLAGS[p.league_id] ?? "⚽";
      return `${flag} ${p.home_team} vs ${p.away_team} → ${p.selection} @${p.odds}`;
    }),
    "",
    `📊 Cuota combinada: @${combinedOdds.toFixed(2)}`,
    "",
    "🔗 galaxyparlay.vercel.app",
    "⚠️ Solo con fines educativos. +18",
  ];
  return lines.join("\n");
}

export function ParlayBuilder({ picks, onRemovePick, onClear }: ParlayBuilderProps) {
  const combinedOdds =
    picks.length > 0
      ? Math.round(picks.reduce((acc, p) => acc * p.odds, 1) * 100) / 100
      : 0;

  const totalKelly =
    picks.length > 0
      ? Math.round(
          (picks.reduce((acc, p) => acc + p.kelly_fraction, 0) / picks.length) *
            1000,
        ) / 1000
      : 0;

  const handleShare = useCallback(() => {
    if (picks.length === 0) return;
    const text = buildShareText(picks, combinedOdds);
    if (navigator.share) {
      navigator
        .share({ title: "Mi Parlay — GalaxyParlay", text })
        .catch(() => {
          // fallback: copy to clipboard
          navigator.clipboard.writeText(text).catch(() => {});
        });
    } else {
      navigator.clipboard.writeText(text).then(() => {
        alert("¡Parlay copiado al portapapeles!");
      }).catch(() => {});
    }
  }, [picks, combinedOdds]);

  return (
    <div className="bg-gray-900/70 border border-gray-700/50 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-gray-800/60 border-b border-gray-700/40">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <span>🎲</span>
          <span>Parlay Builder</span>
          {picks.length > 0 && (
            <span className="px-2 py-0.5 bg-purple-500/30 text-purple-300 rounded-full text-xs">
              {picks.length}
            </span>
          )}
        </h3>
        {picks.length > 0 && (
          <button
            onClick={onClear}
            className="text-xs text-gray-500 hover:text-red-400 transition-colors"
          >
            Limpiar
          </button>
        )}
      </div>

      {/* Empty state */}
      {picks.length === 0 && (
        <div className="px-4 py-6 text-center">
          <p className="text-gray-500 text-sm">
            Agrega picks desde arriba para construir tu parlay
          </p>
        </div>
      )}

      {/* Picks list */}
      {picks.length > 0 && (
        <>
          <div className="divide-y divide-gray-700/30 max-h-48 overflow-y-auto">
            {picks.map((p) => (
              <div
                key={`${p.fixture_id}-${p.market}`}
                className="flex items-center justify-between px-4 py-2.5"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-white truncate">
                    {LEAGUE_FLAGS[p.league_id] ?? "⚽"} {p.home_team} vs {p.away_team}
                  </p>
                  <p className="text-xs text-gray-400 truncate">{p.selection}</p>
                </div>
                <div className="flex items-center gap-3 ml-3">
                  <span className="text-sm font-bold text-white whitespace-nowrap">
                    @{p.odds}
                  </span>
                  <button
                    onClick={() => onRemovePick(p.fixture_id, p.market)}
                    className="text-gray-600 hover:text-red-400 transition-colors text-lg leading-none"
                    aria-label="Eliminar pick"
                  >
                    ×
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Summary */}
          <div className="px-4 py-3 bg-gray-800/40 border-t border-gray-700/40 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400">Cuota combinada</span>
              <span className="text-lg font-black text-white">
                @{combinedOdds.toFixed(2)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400">Kelly promedio</span>
              <span className="text-xs font-semibold text-purple-400">
                {(totalKelly * 100).toFixed(1)}% bankroll
              </span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-2 px-4 py-3 border-t border-gray-700/40">
            <button
              onClick={handleShare}
              className="flex-1 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              <span>📤</span>
              <span>Compartir Parlay</span>
            </button>
          </div>

          {/* Disclaimer */}
          <p className="px-4 pb-3 text-center text-xs text-gray-600">
            Solo con fines educativos • +18
          </p>
        </>
      )}
    </div>
  );
}
