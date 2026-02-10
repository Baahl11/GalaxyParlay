/**
 * LeagueClusterView - Vista de cúmulos por liga
 *
 * Organización:
 * - Cada liga tiene su propio cluster
 * - Colores indican: calidad del pick (A/B/C) + día del match
 * - Layout responsive con agrupación visual clara
 *
 * Esquema de colores:
 * HOY:
 *   - Grade A: Verde brillante (#10b981)
 *   - Grade B: Amarillo/Amber (#f59e0b)
 *   - Grade C: Gris (#6b7280)
 *
 * MAÑANA:
 *   - Grade A: Verde medio (#059669)
 *   - Grade B: Naranja (#ea580c)
 *   - Grade C: Gris oscuro (#4b5563)
 *
 * PRÓXIMOS DÍAS (2-7 días):
 *   - Grade A: Verde oscuro (#047857)
 *   - Grade B: Rojo/Rosa (#dc2626)
 *   - Grade C: Gris muy oscuro (#374151)
 */

"use client";

import type { Fixture } from "@/lib/types";
import { LEAGUE_INFO as leagueInfo } from "@/lib/types";
import { useMemo, useState } from "react";

interface LeagueClusterViewProps {
  fixtures: Fixture[];
  onFixtureClick?: (fixture: Fixture) => void;
}

interface ClusterFixture {
  fixture: Fixture;
  grade: string;
  daysUntilMatch: number;
  color: string;
  urgency: "today" | "tomorrow" | "upcoming";
}

interface LeagueCluster {
  leagueId: number;
  leagueName: string;
  country: string;
  logo?: string;
  fixtures: ClusterFixture[];
  gradeBreakdown: { A: number; B: number; C: number };
}

export function LeagueClusterView({
  fixtures,
  onFixtureClick,
}: LeagueClusterViewProps) {
  const [hoveredFixture, setHoveredFixture] = useState<Fixture | null>(null);

  // Validar que fixtures existe
  if (!fixtures || !Array.isArray(fixtures) || fixtures.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-4xl mb-4">📊</div>
        <p className="text-gray-400">No fixtures available</p>
      </div>
    );
  }

  // Color schemes by urgency + grade
  const getFixtureColor = (grade: string, daysUntil: number): string => {
    // HOY (0 días)
    if (daysUntil === 0) {
      switch (grade) {
        case "A":
          return "#10b981"; // Verde brillante
        case "B":
          return "#f59e0b"; // Amarillo/Amber
        case "C":
          return "#6b7280"; // Gris
        default:
          return "#4b5563"; // Gris oscuro
      }
    }

    // MAÑANA (1 día)
    if (daysUntil === 1) {
      switch (grade) {
        case "A":
          return "#059669"; // Verde medio
        case "B":
          return "#ea580c"; // Naranja
        case "C":
          return "#4b5563"; // Gris oscuro
        default:
          return "#374151"; // Gris muy oscuro
      }
    }

    // PRÓXIMOS DÍAS (2-7 días)
    if (daysUntil >= 2 && daysUntil <= 7) {
      switch (grade) {
        case "A":
          return "#047857"; // Verde oscuro
        case "B":
          return "#dc2626"; // Rojo
        case "C":
          return "#374151"; // Gris muy oscuro
        default:
          return "#1f2937"; // Casi negro
      }
    }

    // MÁS ADELANTE (8+ días)
    switch (grade) {
      case "A":
        return "#065f46"; // Verde muy oscuro
      case "B":
        return "#991b1b"; // Rojo oscuro
      case "C":
        return "#1f2937"; // Casi negro
      default:
        return "#111827"; // Negro
    }
  };

  const getUrgency = (daysUntil: number): "today" | "tomorrow" | "upcoming" => {
    if (daysUntil === 0) return "today";
    if (daysUntil === 1) return "tomorrow";
    return "upcoming";
  };

  // Agrupar fixtures por liga
  const leagueClusters = useMemo((): LeagueCluster[] => {
    const clusterMap = new Map<number, LeagueCluster>();

    fixtures.forEach((fixture) => {
      const leagueId = fixture.league_id;

      if (!clusterMap.has(leagueId)) {
        const info = leagueInfo[leagueId] || {
          name: `League ${leagueId}`,
          country: "International",
          logo: undefined,
        };

        clusterMap.set(leagueId, {
          leagueId,
          leagueName: info.name,
          country: info.country,
          logo: info.logo,
          fixtures: [],
          gradeBreakdown: { A: 0, B: 0, C: 0 },
        });
      }

      const cluster = clusterMap.get(leagueId)!;

      // Calcular días hasta el match
      const matchDate = new Date(fixture.kickoff_time);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      matchDate.setHours(0, 0, 0, 0);
      const daysUntil = Math.floor(
        (matchDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24),
      );

      // Obtener grade principal (match_winner)
      const mainQuality = fixture.quality_scores?.find(
        (q) => q.market_key === "match_winner",
      );
      const grade = mainQuality?.final_grade || "C";

      const color = getFixtureColor(grade, daysUntil);
      const urgency = getUrgency(daysUntil);

      cluster.fixtures.push({
        fixture,
        grade,
        daysUntilMatch: daysUntil,
        color,
        urgency,
      });

      // Actualizar breakdown
      if (grade === "A" || grade === "B" || grade === "C") {
        cluster.gradeBreakdown[grade]++;
      }
    });

    // Ordenar clusters por número de fixtures A+B
    return Array.from(clusterMap.values()).sort((a, b) => {
      const aScore = a.gradeBreakdown.A * 3 + a.gradeBreakdown.B * 1;
      const bScore = b.gradeBreakdown.A * 3 + b.gradeBreakdown.B * 1;
      return bScore - aScore;
    });
  }, [fixtures]);

  const urgencyLabels = {
    today: "🔥 HOY",
    tomorrow: "⏰ MAÑANA",
    upcoming: "📅 PRÓXIMOS",
  };

  const urgencyColors = {
    today: "from-red-500/20 to-orange-500/20 border-red-500/30",
    tomorrow: "from-orange-500/20 to-yellow-500/20 border-orange-500/30",
    upcoming: "from-blue-500/20 to-purple-500/20 border-blue-500/30",
  };

  return (
    <div className="space-y-6">
      {/* Leyenda de colores */}
      <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700/50">
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          🎨 <span>Código de Colores</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* HOY */}
          <div className="space-y-2">
            <div className="text-sm font-semibold text-red-400 flex items-center gap-2">
              🔥 HOY
            </div>
            <div className="flex gap-2">
              <div
                className="flex-1 h-8 rounded flex items-center justify-center text-xs font-bold text-white"
                style={{ backgroundColor: "#10b981" }}
              >
                Grade A
              </div>
              <div
                className="flex-1 h-8 rounded flex items-center justify-center text-xs font-bold text-white"
                style={{ backgroundColor: "#f59e0b" }}
              >
                Grade B
              </div>
              <div
                className="flex-1 h-8 rounded flex items-center justify-center text-xs font-bold text-white"
                style={{ backgroundColor: "#6b7280" }}
              >
                Grade C
              </div>
            </div>
          </div>

          {/* MAÑANA */}
          <div className="space-y-2">
            <div className="text-sm font-semibold text-orange-400 flex items-center gap-2">
              ⏰ MAÑANA
            </div>
            <div className="flex gap-2">
              <div
                className="flex-1 h-8 rounded flex items-center justify-center text-xs font-bold text-white"
                style={{ backgroundColor: "#059669" }}
              >
                Grade A
              </div>
              <div
                className="flex-1 h-8 rounded flex items-center justify-center text-xs font-bold text-white"
                style={{ backgroundColor: "#ea580c" }}
              >
                Grade B
              </div>
              <div
                className="flex-1 h-8 rounded flex items-center justify-center text-xs font-bold text-white"
                style={{ backgroundColor: "#4b5563" }}
              >
                Grade C
              </div>
            </div>
          </div>

          {/* PRÓXIMOS DÍAS */}
          <div className="space-y-2">
            <div className="text-sm font-semibold text-blue-400 flex items-center gap-2">
              📅 PRÓXIMOS (2-7 días)
            </div>
            <div className="flex gap-2">
              <div
                className="flex-1 h-8 rounded flex items-center justify-center text-xs font-bold text-white"
                style={{ backgroundColor: "#047857" }}
              >
                Grade A
              </div>
              <div
                className="flex-1 h-8 rounded flex items-center justify-center text-xs font-bold text-white"
                style={{ backgroundColor: "#dc2626" }}
              >
                Grade B
              </div>
              <div
                className="flex-1 h-8 rounded flex items-center justify-center text-xs font-bold text-white"
                style={{ backgroundColor: "#374151" }}
              >
                Grade C
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Clusters por liga */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {leagueClusters.map((cluster) => (
          <div
            key={cluster.leagueId}
            className="bg-gray-800/50 rounded-xl border border-gray-700/50 overflow-hidden hover:border-purple-500/30 transition-colors"
          >
            {/* Header de la liga */}
            <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 p-4 border-b border-gray-700/50">
              <div className="flex items-center gap-3">
                {cluster.logo && (
                  <img
                    src={cluster.logo}
                    alt={cluster.leagueName}
                    className="w-10 h-10 object-contain"
                  />
                )}
                <div className="flex-1 min-w-0">
                  <h3 className="font-bold text-white truncate">
                    {cluster.leagueName}
                  </h3>
                  <p className="text-xs text-gray-400">{cluster.country}</p>
                </div>
              </div>

              {/* Grade breakdown */}
              <div className="flex gap-2 mt-3">
                {cluster.gradeBreakdown.A > 0 && (
                  <div className="flex items-center gap-1 text-xs">
                    <span className="w-3 h-3 rounded-full bg-green-500"></span>
                    <span className="text-green-400 font-semibold">
                      {cluster.gradeBreakdown.A}×A
                    </span>
                  </div>
                )}
                {cluster.gradeBreakdown.B > 0 && (
                  <div className="flex items-center gap-1 text-xs">
                    <span className="w-3 h-3 rounded-full bg-amber-500"></span>
                    <span className="text-amber-400 font-semibold">
                      {cluster.gradeBreakdown.B}×B
                    </span>
                  </div>
                )}
                {cluster.gradeBreakdown.C > 0 && (
                  <div className="flex items-center gap-1 text-xs">
                    <span className="w-3 h-3 rounded-full bg-gray-500"></span>
                    <span className="text-gray-400 font-semibold">
                      {cluster.gradeBreakdown.C}×C
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Cluster de fixtures (CÚMULO VISUAL) */}
            <div className="p-4">
              <div className="flex flex-wrap gap-2 min-h-[120px]">
                {cluster.fixtures
                  .sort((a, b) => {
                    // Ordenar por urgencia primero, luego por grade
                    if (a.daysUntilMatch !== b.daysUntilMatch) {
                      return a.daysUntilMatch - b.daysUntilMatch;
                    }
                    const gradeOrder = { A: 0, B: 1, C: 2 };
                    return (
                      gradeOrder[a.grade as "A" | "B" | "C"] -
                      gradeOrder[b.grade as "A" | "B" | "C"]
                    );
                  })
                  .map((clusterFixture, index) => {
                    const { fixture, color, urgency, grade, daysUntilMatch } =
                      clusterFixture;
                    const isHovered = hoveredFixture?.id === fixture.id;

                    return (
                      <button
                        key={fixture.id}
                        onClick={() => onFixtureClick?.(fixture)}
                        onMouseEnter={() => setHoveredFixture(fixture)}
                        onMouseLeave={() => setHoveredFixture(null)}
                        className={`
                          relative group
                          transition-all duration-200
                          ${isHovered ? "scale-125 z-10" : "scale-100"}
                        `}
                        title={`${fixture.home_team_name} vs ${fixture.away_team_name}\nGrade ${grade} • ${daysUntilMatch === 0 ? "Hoy" : daysUntilMatch === 1 ? "Mañana" : `En ${daysUntilMatch} días`}`}
                      >
                        {/* Círculo/estrella del pick */}
                        <div
                          className={`
                            w-10 h-10 rounded-full
                            flex items-center justify-center
                            text-xs font-bold text-white
                            shadow-lg
                            ${isHovered ? "shadow-2xl" : ""}
                          `}
                          style={{
                            backgroundColor: color,
                            boxShadow: isHovered
                              ? `0 0 20px ${color}`
                              : `0 0 10px ${color}40`,
                          }}
                        >
                          {grade}
                        </div>

                        {/* Badge de urgencia */}
                        {urgency === "today" && (
                          <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                        )}

                        {/* Tooltip al hover */}
                        {isHovered && (
                          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 rounded-lg text-xs text-white whitespace-nowrap shadow-xl border border-gray-700 z-50">
                            <div className="font-bold">
                              {fixture.home_team_name} vs{" "}
                              {fixture.away_team_name}
                            </div>
                            <div className="text-gray-400 text-xs">
                              Grade {grade} •{" "}
                              {daysUntilMatch === 0
                                ? "🔥 Hoy"
                                : daysUntilMatch === 1
                                  ? "⏰ Mañana"
                                  : `📅 En ${daysUntilMatch} días`}
                            </div>
                            <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-2 h-2 bg-gray-900 rotate-45 -mt-1 border-r border-b border-gray-700" />
                          </div>
                        )}
                      </button>
                    );
                  })}
              </div>

              {/* Footer con stats */}
              <div className="mt-4 pt-3 border-t border-gray-700/50 flex items-center justify-between text-xs">
                <span className="text-gray-400">
                  {cluster.fixtures.length} fixture
                  {cluster.fixtures.length !== 1 ? "s" : ""}
                </span>
                <div className="flex gap-2">
                  {cluster.fixtures.filter((f) => f.urgency === "today")
                    .length > 0 && (
                    <span className="text-red-400 font-semibold">
                      🔥{" "}
                      {
                        cluster.fixtures.filter((f) => f.urgency === "today")
                          .length
                      }
                    </span>
                  )}
                  {cluster.fixtures.filter((f) => f.urgency === "tomorrow")
                    .length > 0 && (
                    <span className="text-orange-400 font-semibold">
                      ⏰{" "}
                      {
                        cluster.fixtures.filter((f) => f.urgency === "tomorrow")
                          .length
                      }
                    </span>
                  )}
                  {cluster.fixtures.filter((f) => f.urgency === "upcoming")
                    .length > 0 && (
                    <span className="text-blue-400 font-semibold">
                      📅{" "}
                      {
                        cluster.fixtures.filter((f) => f.urgency === "upcoming")
                          .length
                      }
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Stats globales */}
      <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700/50">
        <h3 className="text-lg font-bold text-white mb-4">📊 Resumen Global</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-3xl font-black text-green-400">
              {leagueClusters.reduce((sum, c) => sum + c.gradeBreakdown.A, 0)}
            </div>
            <div className="text-sm text-gray-400">Grade A Picks</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-black text-amber-400">
              {leagueClusters.reduce((sum, c) => sum + c.gradeBreakdown.B, 0)}
            </div>
            <div className="text-sm text-gray-400">Grade B Picks</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-black text-red-400">
              {
                fixtures.filter((f) => {
                  const matchDate = new Date(f.kickoff_time);
                  const today = new Date();
                  today.setHours(0, 0, 0, 0);
                  matchDate.setHours(0, 0, 0, 0);
                  return matchDate.getTime() === today.getTime();
                }).length
              }
            </div>
            <div className="text-sm text-gray-400">🔥 Hoy</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-black text-purple-400">
              {leagueClusters.length}
            </div>
            <div className="text-sm text-gray-400">Ligas Activas</div>
          </div>
        </div>
      </div>
    </div>
  );
}
