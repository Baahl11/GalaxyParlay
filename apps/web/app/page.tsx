"use client";

// GalaxyParlay — Main Page v3.0 (Galaxy + Picks Hybrid)
import {
  FixtureList,
  GalaxyCanvas,
  LeagueFilter,
  MatchDrawer,
  ModelAccuracy,
  ParlayBuilder,
  StatsCard,
  TodayPicks,
} from "@/components";
import { getFixturesWithQuality, getStats, type ValueBet } from "@/lib/api";
import type { Fixture, StatsResponse } from "@/lib/types";
import { useCallback, useEffect, useState } from "react";

type ViewKey = "picks" | "fixtures" | "stats";

export default function Home() {
  const [activeView, setActiveView] = useState<ViewKey>("picks");
  const [fixtures, setFixtures] = useState<Fixture[]>([]);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loadingFixtures, setLoadingFixtures] = useState(true);
  const [selectedLeague, setSelectedLeague] = useState<number | null>(null);

  // Galaxy interaction
  const [highlightedFixtureId, setHighlightedFixtureId] = useState<
    number | null
  >(null);

  // Parlay state
  const [parlayPicks, setParlayPicks] = useState<ValueBet[]>([]);

  // Match Drawer
  const [selectedFixture, setSelectedFixture] = useState<Fixture | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Track loaded picks for cross-referencing with galaxy clicks
  const [allPicks, setAllPicks] = useState<ValueBet[]>([]);

  useEffect(() => {
    setLoadingFixtures(true);
    Promise.all([
      getFixturesWithQuality({ status: "NS", limit: 200 }),
      getStats(),
    ])
      .then(([fixturesData, statsData]) => {
        setFixtures(fixturesData || []);
        setStats(statsData);
      })
      .catch(console.error)
      .finally(() => setLoadingFixtures(false));
  }, []);

  const handleFixtureClick = useCallback((fixture: Fixture) => {
    setSelectedFixture(fixture);
    setDrawerOpen(true);
    setHighlightedFixtureId(fixture.id);
  }, []);

  const handleGalaxyClick = useCallback((fixture: Fixture) => {
    setHighlightedFixtureId(fixture.id);
    setSelectedFixture(fixture);
    setDrawerOpen(true);
  }, []);

  const handleToggleParlay = useCallback((bet: ValueBet) => {
    setParlayPicks((prev) => {
      const key = `${bet.fixture_id}-${bet.market}`;
      const exists = prev.some((p) => `${p.fixture_id}-${p.market}` === key);
      return exists
        ? prev.filter((p) => `${p.fixture_id}-${p.market}` !== key)
        : [...prev, bet];
    });
  }, []);

  const handleRemoveFromParlay = useCallback(
    (fixtureId: number, market: string) => {
      setParlayPicks((prev) =>
        prev.filter(
          (p) => !(p.fixture_id === fixtureId && p.market === market),
        ),
      );
    },
    [],
  );

  const handlePicksLoaded = useCallback((bets: ValueBet[]) => {
    setAllPicks(bets);
  }, []);

  const navTabs: { key: ViewKey; label: string; icon: string }[] = [
    { key: "picks", label: "Picks del Día", icon: "🎯" },
    { key: "fixtures", label: "Partidos", icon: "📅" },
    { key: "stats", label: "Precisión", icon: "📊" },
  ];

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col">
      {/* ── Top Nav ──────────────────────────────────────────────── */}
      <header className="border-b border-gray-800/60 bg-gray-950/95 backdrop-blur-sm sticky top-0 z-20">
        <div className="max-w-screen-2xl mx-auto px-4 py-3 flex items-center gap-4">
          {/* Brand */}
          <div className="flex items-center gap-2 mr-4">
            <span className="text-2xl">🌌</span>
            <span className="font-black text-lg bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
              GalaxyParlay
            </span>
          </div>

          {/* Nav tabs */}
          <nav className="flex gap-1">
            {navTabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveView(tab.key)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  activeView === tab.key
                    ? "bg-purple-600/30 text-white border border-purple-500/40"
                    : "text-gray-400 hover:text-white hover:bg-gray-800/60"
                }`}
              >
                <span>{tab.icon}</span>
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            ))}
          </nav>

          {/* Right: parlay badge */}
          <div className="ml-auto flex items-center gap-3">
            {parlayPicks.length > 0 && (
              <span className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 bg-purple-600/20 border border-purple-500/30 rounded-lg text-sm text-purple-300">
                🎲 {parlayPicks.length} pick
                {parlayPicks.length !== 1 ? "s" : ""} @
                {parlayPicks.reduce((a, b) => a * b.odds, 1).toFixed(2)}
              </span>
            )}
            <span className="text-xs text-gray-600">+18 · Educativo</span>
          </div>
        </div>
      </header>

      {/* ── Main Content ─────────────────────────────────────────── */}
      {activeView === "picks" && (
        <div className="flex-1 flex overflow-hidden max-w-screen-2xl mx-auto w-full">
          {/* Left: Galaxy Canvas — hidden on small screens */}
          <aside className="hidden xl:flex xl:w-[42%] flex-col border-r border-gray-800/60 overflow-hidden">
            <div className="px-4 pt-4 pb-2 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-gray-400 flex items-center gap-2">
                <span>🌌</span> Mapa de Partidos
              </h2>
              {loadingFixtures && (
                <span className="text-xs text-gray-600 animate-pulse">
                  Cargando…
                </span>
              )}
            </div>
            <div className="flex-1 overflow-hidden px-2 pb-2">
              {!loadingFixtures && fixtures.length > 0 ? (
                <GalaxyCanvas
                  fixtures={fixtures}
                  onFixtureClick={handleGalaxyClick}
                />
              ) : (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="text-5xl mb-3 animate-pulse">🌌</div>
                    <p className="text-gray-600 text-sm">
                      {loadingFixtures ? "Cargando galaxy…" : "Sin partidos"}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </aside>

          {/* Right: Picks + Parlay */}
          <main className="flex-1 flex flex-col overflow-hidden">
            {/* Picks list — scrollable */}
            <div className="flex-1 overflow-y-auto px-4 pt-4 pb-2">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <span>🎯</span> Picks del Día
                </h2>
                {stats && (
                  <span className="text-xs text-gray-500">
                    {stats.predictions?.grade_a ?? 0} grado A
                  </span>
                )}
              </div>
              <TodayPicks
                parlayPicks={parlayPicks}
                highlightedFixtureId={highlightedFixtureId}
                onToggleParlay={handleToggleParlay}
                onClickFixture={(fid: number) => {
                  const fx = fixtures.find((f) => f.id === fid);
                  if (fx) handleFixtureClick(fx);
                }}
                onPicksLoaded={handlePicksLoaded}
              />
            </div>

            {/* Parlay builder — sticky bottom */}
            <div className="px-4 pb-4 pt-2 border-t border-gray-800/60 bg-gray-950/80 backdrop-blur-sm">
              <ParlayBuilder
                picks={parlayPicks}
                onRemovePick={handleRemoveFromParlay}
                onClear={() => setParlayPicks([])}
              />
            </div>
          </main>
        </div>
      )}

      {activeView === "fixtures" && (
        <div className="flex-1 max-w-screen-xl mx-auto w-full px-4 py-6">
          <div className="mb-4">
            <LeagueFilter
              selectedLeague={selectedLeague}
              onSelect={setSelectedLeague}
            />
          </div>
          {loadingFixtures ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {[...Array(6)].map((_, i) => (
                <div
                  key={i}
                  className="h-48 bg-gray-800/40 rounded-2xl animate-pulse"
                />
              ))}
            </div>
          ) : (
            <FixtureList
              fixtures={
                selectedLeague
                  ? fixtures.filter((f) => f.league_id === selectedLeague)
                  : fixtures
              }
              title={`Próximos partidos${selectedLeague ? " · filtrado" : ""}`}
              onFixtureClick={handleFixtureClick}
            />
          )}
        </div>
      )}

      {activeView === "stats" && (
        <div className="flex-1 max-w-screen-xl mx-auto w-full px-4 py-6 space-y-6">
          {stats && <StatsCard stats={stats} />}
          <ModelAccuracy />
        </div>
      )}

      {/* Match Drawer */}
      <MatchDrawer
        fixture={selectedFixture}
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />

      {/* Footer */}
      <footer className="border-t border-gray-800/60 py-4 mt-auto">
        <p className="text-center text-xs text-gray-600">
          GalaxyParlay · Powered by AI & API-Football · Solo con fines
          educativos · +18
        </p>
      </footer>
    </div>
  );
}
