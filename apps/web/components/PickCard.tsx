"use client";

import type { ValueBet } from "@/lib/api";
import { LEAGUE_FLAGS, LEAGUE_NAMES } from "@/lib/types";

interface PickCardProps {
  bet: ValueBet;
  inParlay?: boolean;
  highlighted?: boolean;
  onToggleParlay: (bet: ValueBet) => void;
  onClickFixture?: (fixtureId: number) => void;
}

const MARKET_LABELS: Record<string, string> = {
  match_winner: "Match Result",
  over_under_2_5: "Over/Under 2.5",
  both_teams_score: "Both Teams Score",
};

const GRADE_STYLES: Record<string, { bg: string; text: string; bar: string }> =
  {
    S: {
      bg: "bg-fuchsia-500/20 border-fuchsia-500/40",
      text: "text-fuchsia-400",
      bar: "bg-fuchsia-500",
    },
    A: {
      bg: "bg-green-500/20 border-green-500/40",
      text: "text-green-400",
      bar: "bg-green-500",
    },
    B: {
      bg: "bg-blue-500/20 border-blue-500/40",
      text: "text-blue-400",
      bar: "bg-blue-500",
    },
    C: {
      bg: "bg-yellow-500/20 border-yellow-500/40",
      text: "text-yellow-400",
      bar: "bg-yellow-500",
    },
    D: {
      bg: "bg-orange-500/20 border-orange-500/40",
      text: "text-orange-400",
      bar: "bg-orange-500",
    },
  };

function formatTime(isoString: string): string {
  const d = new Date(isoString);
  const now = new Date();
  const diffMs = d.getTime() - now.getTime();
  const diffH = Math.floor(diffMs / 3_600_000);
  const diffD = Math.floor(diffH / 24);

  const timeStr = d.toLocaleTimeString("es-ES", {
    hour: "2-digit",
    minute: "2-digit",
  });
  const dateStr = d.toLocaleDateString("es-ES", {
    weekday: "short",
    day: "numeric",
    month: "short",
  });

  if (diffD === 0) return `Hoy ${timeStr}`;
  if (diffD === 1) return `Mañana ${timeStr}`;
  return `${dateStr} ${timeStr}`;
}

export function PickCard({
  bet,
  inParlay = false,
  highlighted = false,
  onToggleParlay,
  onClickFixture,
}: PickCardProps) {
  const gradeStyle = GRADE_STYLES[bet.grade] ?? GRADE_STYLES["C"];
  const marketLabel = MARKET_LABELS[bet.market] ?? bet.market;
  const leagueFlag = LEAGUE_FLAGS[bet.league_id] ?? "⚽";
  const leagueName = LEAGUE_NAMES[bet.league_id] ?? `Liga ${bet.league_id}`;
  const probPct = Math.round(bet.model_prob * 100);
  const evPct = (bet.ev * 100).toFixed(1);
  const edgePct = (bet.edge * 100).toFixed(1);
  const isModelOdds = bet.odds_source === "model";

  return (
    <div
      className={`
        relative rounded-xl border p-4 transition-all duration-200 cursor-pointer
        ${highlighted ? "ring-2 ring-purple-500 ring-offset-1 ring-offset-gray-950" : ""}
        ${inParlay ? "bg-purple-900/20 border-purple-500/40" : "bg-gray-800/60 border-gray-700/50 hover:border-gray-600/70"}
      `}
      onClick={() => onClickFixture?.(bet.fixture_id)}
    >
      {/* League + Time row */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-400 flex items-center gap-1">
          <span>{leagueFlag}</span>
          <span>{leagueName}</span>
        </span>
        <span className="text-xs text-gray-500">
          {formatTime(bet.kickoff_time)}
        </span>
      </div>

      {/* Match */}
      <div className="mb-3">
        <p className="font-semibold text-white text-sm leading-tight">
          {bet.home_team} <span className="text-gray-500">vs</span>{" "}
          {bet.away_team}
        </p>
      </div>

      {/* Market + Probability bar */}
      <div className="mb-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-gray-400">{marketLabel}</span>
          <span className={`text-xs font-bold ${gradeStyle.text}`}>
            {bet.selection}
          </span>
        </div>
        <div className="h-2 bg-gray-700/60 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${gradeStyle.bar}`}
            style={{ width: `${probPct}%` }}
          />
        </div>
        <div className="flex justify-between mt-1">
          <span className="text-xs text-gray-500">Prob. modelo</span>
          <span className={`text-xs font-semibold ${gradeStyle.text}`}>
            {probPct}%
          </span>
        </div>
      </div>

      {/* Stats row */}
      <div className="flex items-center gap-2 mb-3">
        <span
          className={`px-2 py-0.5 rounded-full text-xs font-bold border ${gradeStyle.bg} ${gradeStyle.text}`}
        >
          Grado {bet.grade}
        </span>
        {isModelOdds ? (
          <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30">
            Cuota modelo
          </span>
        ) : (
          <>
            <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              EV +{evPct}%
            </span>
            <span className="px-2 py-0.5 rounded-full text-xs text-gray-400 bg-gray-700/40 border border-gray-600/30">
              Edge +{edgePct}%
            </span>
          </>
        )}
        <span className="ml-auto text-sm font-bold text-white">
          @{bet.odds}
        </span>
      </div>

      {/* Add to Parlay button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onToggleParlay(bet);
        }}
        className={`
          w-full py-1.5 rounded-lg text-xs font-semibold transition-all duration-200
          ${
            inParlay
              ? "bg-purple-600 hover:bg-purple-700 text-white"
              : "bg-gray-700/60 hover:bg-purple-500/30 text-gray-300 hover:text-white border border-gray-600/40 hover:border-purple-500/40"
          }
        `}
      >
        {inParlay ? "✓ En el Parlay" : "+ Agregar al Parlay"}
      </button>
    </div>
  );
}
