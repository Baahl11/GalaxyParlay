'use client';

import {
    FixtureList,
    GalaxyCanvas,
    MatchDrawer,
    PlayerPropsSection,
    StatsCard,
    ValueBetList
} from '@/components';
import { getFixtures, getStats } from '@/lib/api';
import type { Fixture, StatsResponse } from '@/lib/types';
import { useEffect, useState } from 'react';

type TabKey = 'galaxy' | 'fixtures' | 'valuebets' | 'players';

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabKey>('galaxy');
  const [fixtures, setFixtures] = useState<Fixture[]>([]);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Match Drawer State
  const [selectedFixture, setSelectedFixture] = useState<Fixture | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [fixturesData, statsData] = await Promise.all([
        getFixtures({ limit: 100 }),
        getStats()
      ]);
      setFixtures(fixturesData);
      setStats(statsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleFixtureClick = (fixture: Fixture) => {
    setSelectedFixture(fixture);
    setDrawerOpen(true);
  };

  const tabs: { key: TabKey; label: string; icon: string }[] = [
    { key: 'galaxy', label: 'Galaxy View', icon: '🌌' },
    { key: 'fixtures', label: 'List View', icon: '📅' },
    { key: 'valuebets', label: 'Value Bets', icon: '💎' },
    { key: 'players', label: 'Player Props', icon: '⚽' },
  ];

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-purple-900/20 via-transparent to-transparent" />
        <div className="max-w-7xl mx-auto px-4 py-12 sm:py-16 relative">
          <div className="text-center">
            <h1 className="text-5xl md:text-7xl font-black bg-gradient-to-r from-purple-400 via-pink-500 to-red-500 bg-clip-text text-transparent mb-4">
              ParlayGalaxy
            </h1>
            <p className="text-xl md:text-2xl text-gray-400 mb-2">
              Smart Football Betting Intelligence
            </p>
            <p className="text-gray-500 max-w-2xl mx-auto mb-6">
              AI-powered predictions with ensemble ML models, real-time odds tracking, 
              and quality grades to maximize your edge.
            </p>
            
            {/* Refresh Button */}
            <button
              onClick={loadData}
              disabled={loading}
              className="inline-flex items-center gap-2 px-4 py-2 bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 rounded-lg transition-colors disabled:opacity-50"
            >
              <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh Data
            </button>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      {stats && (
        <div className="max-w-7xl mx-auto px-4 -mt-4 mb-8">
          <StatsCard stats={stats} />
        </div>
      )}

      {/* Main Tabs */}
      <div className="max-w-7xl mx-auto px-4 mb-6">
        <div className="flex gap-2 p-1 bg-gray-800/50 rounded-xl border border-gray-700/50">
          {tabs.map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab.key
                  ? 'bg-gradient-to-r from-purple-500/30 to-pink-500/30 text-white border border-purple-500/30'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700/30'
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
              {tab.key === 'fixtures' && fixtures.length > 0 && (
                <span className="ml-1 px-2 py-0.5 bg-gray-700/50 rounded-full text-xs">
                  {fixtures.length}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="max-w-7xl mx-auto px-4 pb-20">
        {error && (
          <div className="text-center py-12 bg-red-900/20 rounded-xl border border-red-500/30 mb-6">
            <div className="text-4xl mb-4">⚠️</div>
            <h3 className="text-xl font-semibold text-red-400 mb-2">Connection Error</h3>
            <p className="text-gray-500 mb-4">{error}</p>
            <button
              onClick={loadData}
              className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors"
            >
              Retry
            </button>
          </div>
        )}

        {activeTab === 'galaxy' && (
          <>
            {loading ? (
              <div className="flex items-center justify-center h-96 bg-gray-800/50 rounded-2xl">
                <div className="text-center">
                  <div className="text-6xl mb-4 animate-pulse">🌌</div>
                  <p className="text-gray-400">Loading Galaxy...</p>
                </div>
              </div>
            ) : (
              <div>
                <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
                  <span>🌌</span>
                  <span>Galaxy View</span>
                  <span className="text-sm font-normal text-gray-500 ml-2">
                    Hover over stars to see fixtures • Click to view details
                  </span>
                </h2>
                <GalaxyCanvas 
                  fixtures={fixtures}
                  onFixtureClick={handleFixtureClick}
                />
              </div>
            )}
          </>
        )}

        {activeTab === 'fixtures' && (
          <>
            {loading ? (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="h-48 bg-gray-800/50 rounded-2xl animate-pulse" />
                ))}
              </div>
            ) : (
              <FixtureList 
                fixtures={fixtures} 
                title="Upcoming Fixtures"
                onFixtureClick={handleFixtureClick}
              />
            )}
          </>
        )}

        {activeTab === 'valuebets' && (
          <ValueBetList limit={20} />
        )}

        {activeTab === 'players' && (
          <PlayerPropsSection />
        )}
      </div>

      {/* Match Drawer */}
      <MatchDrawer 
        fixture={selectedFixture}
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />

      {/* Footer */}
      <footer className="border-t border-gray-800 py-8">
        <div className="max-w-7xl mx-auto px-4 text-center text-gray-500 text-sm">
          <p>🚀 ParlayGalaxy v1.0.0 • Powered by AI & API-Football</p>
          <p className="mt-2">⚠️ For entertainment purposes only. Please gamble responsibly.</p>
        </div>
      </footer>
    </main>
  );
}
