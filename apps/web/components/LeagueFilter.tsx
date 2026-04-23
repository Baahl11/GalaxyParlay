"use client";

import { LEAGUE_FLAGS } from "@/lib/types";

interface LeagueFilterProps {
  selectedLeague: number | null;
  onSelect: (leagueId: number | null) => void;
}

const LEAGUES = [
  { id: 39, name: "Premier League" },
  { id: 140, name: "La Liga" },
  { id: 78, name: "Bundesliga" },
  { id: 135, name: "Serie A" },
  { id: 61, name: "Ligue 1" },
  { id: 2, name: "Champions League" },
  { id: 3, name: "Europa League" },
  { id: 848, name: "Conference League" },
  { id: 94, name: "Primeira Liga" },
  { id: 88, name: "Eredivisie" },
  { id: 203, name: "Super Lig" },
  { id: 144, name: "Belgian Pro League" },
  { id: 71, name: "Brasileirao" },
  { id: 262, name: "Liga MX" },
  { id: 128, name: "Liga Profesional" },
  { id: 253, name: "MLS" },
  { id: 13, name: "Copa Libertadores" },
  { id: 11, name: "Copa Sudamericana" },
];

export function LeagueFilter({ selectedLeague, onSelect }: LeagueFilterProps) {
  return (
    <div className="flex flex-wrap gap-2">
      <button
        onClick={() => onSelect(null)}
        className={`
          px-4 py-2 rounded-full text-sm font-medium transition-all
          ${
            selectedLeague === null
              ? "bg-purple-600 text-white"
              : "bg-gray-800 text-gray-400 hover:bg-gray-700"
          }
        `}
      >
        All Leagues
      </button>
      {LEAGUES.map((league) => (
        <button
          key={league.id}
          onClick={() => onSelect(league.id)}
          className={`
            px-4 py-2 rounded-full text-sm font-medium transition-all
            flex items-center gap-2
            ${
              selectedLeague === league.id
                ? "bg-purple-600 text-white"
                : "bg-gray-800 text-gray-400 hover:bg-gray-700"
            }
          `}
        >
          <span>{LEAGUE_FLAGS[league.id]}</span>
          <span className="hidden sm:inline">{league.name}</span>
        </button>
      ))}
    </div>
  );
}
