'use client';

import { useEffect, useState } from 'react';
import { ValueBetCard, ValueBetData } from './ValueBetCard';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://galaxyparlay-production.up.railway.app';

interface ValueBetsResponse {
  data: ValueBetData[];
  count: number;
  summary: {
    fixtures_analyzed: number;
    value_bets_found: number;
    avg_edge: number;
    avg_ev: number;
  };
}

interface ValueBetListProps {
  limit?: number;
  compact?: boolean;
}

export function ValueBetList({ limit = 10, compact = false }: ValueBetListProps) {
  const [valueBets, setValueBets] = useState<ValueBetData[]>([]);
  const [summary, setSummary] = useState<ValueBetsResponse['summary'] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [minEdge, setMinEdge] = useState(0.03);
  const [minEv, setMinEv] = useState(0.02);

  useEffect(() => {
    fetchValueBets();
  }, [minEdge, minEv, limit]);

  const fetchValueBets = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        min_edge: minEdge.toString(),
        min_ev: minEv.toString(),
        limit: limit.toString(),
      });
      
      const response = await fetch(`${API_BASE_URL}/api/value-bets?${params}`);
      if (!response.ok) throw new Error('Failed to fetch value bets');
      
      const data: ValueBetsResponse = await response.json();
      setValueBets(data.data);
      setSummary(data.summary);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-400">
        <p>Error loading value bets: {error}</p>
        <button 
          onClick={fetchValueBets}
          className="mt-4 px-4 py-2 bg-purple-600 rounded-lg hover:bg-purple-500 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with filters */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            💎 Value Bets
            {summary && (
              <span className="text-sm font-normal text-gray-400">
                ({summary.value_bets_found} found)
              </span>
            )}
          </h2>
          {summary && summary.avg_ev > 0 && (
            <p className="text-sm text-gray-400">
              Avg Edge: +{(summary.avg_edge * 100).toFixed(1)}% • 
              Avg EV: +{(summary.avg_ev * 100).toFixed(1)}%
            </p>
          )}
        </div>

        {/* Quick filters */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => { setMinEdge(0.03); setMinEv(0.02); }}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
              minEdge === 0.03 ? 'bg-green-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            All Value
          </button>
          <button
            onClick={() => { setMinEdge(0.05); setMinEv(0.05); }}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
              minEdge === 0.05 ? 'bg-green-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            5%+ Edge
          </button>
          <button
            onClick={() => { setMinEdge(0.10); setMinEv(0.08); }}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
              minEdge === 0.10 ? 'bg-green-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            High Value
          </button>
        </div>
      </div>

      {/* Value Bets Grid */}
      {valueBets.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <div className="text-4xl mb-4">🔍</div>
          <p>No value bets found with current filters</p>
          <p className="text-sm mt-2">Try lowering the minimum edge or EV thresholds</p>
        </div>
      ) : compact ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {valueBets.map((vb, idx) => (
            <ValueBetCard key={`${vb.fixture_id}-${vb.selection}-${idx}`} valueBet={vb} compact />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {valueBets.map((vb, idx) => (
            <ValueBetCard key={`${vb.fixture_id}-${vb.selection}-${idx}`} valueBet={vb} />
          ))}
        </div>
      )}
    </div>
  );
}
