"use client";

import { Fixture, LEAGUE_NAMES } from "@/lib/types";
import { useMemo, useState } from "react";

interface NetworkGraphViewProps {
  fixtures: Fixture[];
  onFixtureClick?: (fixture: Fixture) => void;
}

const getGradeColor = (grade: string) => {
  switch (grade) {
    case "A":
      return "bg-emerald-500/20 text-emerald-400 border-emerald-500/40";
    case "B":
      return "bg-amber-500/20 text-amber-400 border-amber-500/40";
    case "C":
      return "bg-gray-500/20 text-gray-400 border-gray-500/40";
    default:
      return "bg-gray-500/20 text-gray-400 border-gray-500/40";
  }
};

const getDaysUntil = (date: string): number => {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const matchDate = new Date(date);
  matchDate.setHours(0, 0, 0, 0);
  return Math.floor(
    (matchDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24),
  );
};

export function NetworkGraphView({
  fixtures,
  onFixtureClick,
}: NetworkGraphViewProps) {
  const [expandedDay, setExpandedDay] = useState<string | null>("today");

  // Agrupar por día y luego por liga - MEMOIZADO
  const groupedData = useMemo(() => {
    const today: Map<number, Fixture[]> = new Map();
    const tomorrow: Map<number, Fixture[]> = new Map();
    const upcoming: Map<number, Fixture[]> = new Map();

    // Validar que fixtures existe y es un array
    if (!fixtures || !Array.isArray(fixtures)) {
      return { today, tomorrow, upcoming };
    }

    fixtures.forEach((fixture) => {
      const daysUntil = getDaysUntil(fixture.kickoff_time);
      let targetMap: Map<number, Fixture[]>;

      if (daysUntil === 0) targetMap = today;
      else if (daysUntil === 1) targetMap = tomorrow;
      else if (daysUntil >= 2 && daysUntil <= 7) targetMap = upcoming;
      else return;

      if (!targetMap.has(fixture.league_id)) {
        targetMap.set(fixture.league_id, []);
      }
      targetMap.get(fixture.league_id)!.push(fixture);
    });

    return { today, tomorrow, upcoming };
  }, [fixtures]);

  const renderLeagueCard = (leagueId: number, leagueFixtures: Fixture[]) => {
    const leagueName = LEAGUE_NAMES[leagueId] || `League ${leagueId}`;

    // Calcular distribución de grades basado en predictions
    const gradeDistribution = leagueFixtures.reduce(
      (acc, f) => {
        // Obtener el mejor grade de las predicciones del fixture
        const bestGrade = f.predictions?.[0]?.quality_grade || "B";
        acc[bestGrade] = (acc[bestGrade] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>,
    );

    return (
      <div
        key={leagueId}
        className="bg-gray-800/50 border border-gray-700/50 rounded-lg p-4 hover:border-gray-600/50 transition-all hover:shadow-lg hover:shadow-purple-500/10"
      >
        <div className="flex items-start justify-between mb-3">
          <div>
            <h3 className="font-bold text-white text-lg">{leagueName}</h3>
            <p className="text-sm text-gray-400">
              {leagueFixtures.length} partidos
            </p>
          </div>
          <div className="flex gap-1">
            {Object.entries(gradeDistribution).map(([grade, count]) => (
              <div
                key={grade}
                className={`px-2 py-1 rounded text-xs font-bold border ${getGradeColor(grade)}`}
              >
                {grade} ×{count}
              </div>
            ))}
          </div>
        </div>

        {/* Lista de partidos */}
        <div className="space-y-2">
          {leagueFixtures.slice(0, 5).map((fixture) => {
            const matchTime = new Date(fixture.kickoff_time).toLocaleTimeString(
              "es-ES",
              {
                hour: "2-digit",
                minute: "2-digit",
              },
            );
            const grade = fixture.predictions?.[0]?.quality_grade || "B";

            return (
              <button
                key={fixture.id}
                onClick={() => onFixtureClick?.(fixture)}
                className="w-full text-left p-3 bg-gray-900/50 rounded border border-gray-700/30 hover:border-purple-500/50 hover:bg-gray-900/80 transition-all group"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="text-sm font-medium text-white group-hover:text-purple-400 transition-colors">
                      {fixture.home_team_name} vs {fixture.away_team_name}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {matchTime}
                    </div>
                  </div>
                  <div
                    className={`px-3 py-1 rounded-full text-xs font-bold border ${getGradeColor(grade)}`}
                  >
                    {grade}
                  </div>
                </div>
              </button>
            );
          })}

          {leagueFixtures.length > 5 && (
            <div className="text-xs text-gray-500 text-center pt-2">
              +{leagueFixtures.length - 5} más
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderDaySection = (
    dayKey: string,
    title: string,
    icon: string,
    leagueMap: Map<number, Fixture[]>,
    accentColor: string,
  ) => {
    const totalMatches = Array.from(leagueMap.values()).reduce(
      (sum, arr) => sum + arr.length,
      0,
    );
    const isExpanded = expandedDay === dayKey;

    if (totalMatches === 0) return null;

    return (
      <div className="relative">
        {/* Timeline dot */}
        <div className="absolute left-0 top-3 w-4 h-4 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 border-4 border-gray-950 z-10" />

        {/* Day header */}
        <button
          onClick={() => setExpandedDay(isExpanded ? null : dayKey)}
          className="w-full text-left pl-8 pr-4 py-3 mb-4 bg-gray-800/30 border border-gray-700/30 rounded-lg hover:bg-gray-800/50 transition-all"
        >
          <div className="flex items-center justify-between">
            <div>
              <h2
                className={`text-xl font-black ${accentColor} flex items-center gap-2`}
              >
                <span>{icon}</span>
                <span>{title}</span>
              </h2>
              <p className="text-sm text-gray-400 mt-1">
                {leagueMap.size} ligas • {totalMatches} partidos
              </p>
            </div>
            <div className="text-gray-400">{isExpanded ? "▼" : "▶"}</div>
          </div>
        </button>

        {/* League cards */}
        {isExpanded && (
          <div className="pl-8 space-y-3 mb-6">
            {Array.from(leagueMap.entries())
              .sort((a, b) => b[1].length - a[1].length)
              .map(([leagueId, leagueFixtures]) =>
                renderLeagueCard(leagueId, leagueFixtures),
              )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="relative w-full h-full overflow-y-auto">
      {/* Timeline line */}
      <div className="absolute left-2 top-0 bottom-0 w-0.5 bg-gradient-to-b from-purple-500 via-pink-500 to-purple-500 opacity-30" />

      <div className="max-w-5xl mx-auto p-8 space-y-6">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-black bg-gradient-to-r from-purple-400 via-pink-500 to-purple-600 bg-clip-text text-transparent mb-2">
            Timeline View
          </h1>
          <p className="text-gray-400">Partidos organizados por fecha y liga</p>
        </div>

        {/* Timeline sections */}
        {renderDaySection(
          "today",
          "HOY",
          "🔥",
          groupedData.today,
          "text-red-400",
        )}
        {renderDaySection(
          "tomorrow",
          "MAÑANA",
          "⏰",
          groupedData.tomorrow,
          "text-orange-400",
        )}
        {renderDaySection(
          "upcoming",
          "PRÓXIMOS DÍAS",
          "📅",
          groupedData.upcoming,
          "text-blue-400",
        )}

        {/* Empty state */}
        {groupedData.today.size === 0 &&
          groupedData.tomorrow.size === 0 &&
          groupedData.upcoming.size === 0 && (
            <div className="text-center py-16">
              <div className="text-6xl mb-4 opacity-50">📭</div>
              <p className="text-gray-500">No hay partidos disponibles</p>
            </div>
          )}
      </div>
    </div>
  );
}
