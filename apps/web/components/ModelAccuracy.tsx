"use client";

import { getBacktestResults, BacktestData } from "@/lib/api";
import { useEffect, useState } from "react";

export function ModelAccuracy() {
  const [data, setData] = useState<BacktestData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getBacktestResults()
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <div className="text-gray-400 animate-pulse">Loading accuracy data…</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-12 bg-gray-800/30 rounded-2xl border border-gray-700/50">
        <div className="text-4xl mb-3">📊</div>
        <p className="text-gray-400">No backtesting data available yet.</p>
        <p className="text-gray-500 text-sm mt-1">Results will appear after live matches complete.</p>
      </div>
    );
  }

  const { summary, new_model, by_market } = data;
  const accuracyPct = Math.round(new_model.accuracy * 100 * 10) / 10;
  const brierPct = Math.round(new_model.brier_score * 100 * 10) / 10;

  const marketRows = Object.entries(by_market ?? {})
    .filter(([, v]) => v.sample_size > 0)
    .sort(([, a], [, b]) => b.new_accuracy - a.new_accuracy)
    .slice(0, 10);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-500 to-purple-600 mb-2">
          📊 Model Accuracy
        </h2>
        <p className="text-gray-400 text-sm">
          Backtested on <span className="text-white font-semibold">{summary.fixtures_tested.toLocaleString()}</span> historical fixtures
          &nbsp;·&nbsp;
          <span className="text-white font-semibold">{summary.predictions_tested.toLocaleString()}</span> predictions
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gray-800/50 rounded-2xl border border-gray-700/50 p-6 text-center">
          <div className="text-4xl font-black text-green-400">{accuracyPct}%</div>
          <div className="text-gray-400 text-sm mt-1">Overall Accuracy</div>
          <div className="text-gray-500 text-xs mt-1">% of correct picks</div>
        </div>
        <div className="bg-gray-800/50 rounded-2xl border border-gray-700/50 p-6 text-center">
          <div className="text-4xl font-black text-blue-400">{brierPct}%</div>
          <div className="text-gray-400 text-sm mt-1">Brier Score</div>
          <div className="text-gray-500 text-xs mt-1">Calibration (lower = better)</div>
        </div>
        <div className="bg-gray-800/50 rounded-2xl border border-gray-700/50 p-6 text-center">
          <div className="text-4xl font-black text-purple-400">{summary.markets_tested}</div>
          <div className="text-gray-400 text-sm mt-1">Markets Tested</div>
          <div className="text-gray-500 text-xs mt-1">Betting market types</div>
        </div>
      </div>

      {/* Per-market breakdown */}
      {marketRows.length > 0 && (
        <div className="bg-gray-800/50 rounded-2xl border border-gray-700/50 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-700/50">
            <h3 className="text-white font-semibold">Accuracy by Market</h3>
          </div>
          <div className="divide-y divide-gray-700/30">
            {marketRows.map(([market, stats]) => {
              const pct = Math.round(stats.new_accuracy * 100 * 10) / 10;
              const barWidth = Math.round(stats.new_accuracy * 100);
              return (
                <div key={market} className="px-6 py-3 flex items-center gap-4">
                  <div className="w-52 text-gray-300 text-sm truncate">
                    {market.replace(/_/g, " ")}
                  </div>
                  <div className="flex-1 bg-gray-700/50 rounded-full h-2">
                    <div
                      className="h-2 rounded-full bg-gradient-to-r from-purple-500 to-pink-500"
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>
                  <div className="w-16 text-right text-white font-semibold text-sm">{pct}%</div>
                  <div className="w-20 text-right text-gray-500 text-xs">n={stats.sample_size}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <p className="text-center text-gray-600 text-xs">
        ⚠️ Historical performance does not guarantee future results. Gamble responsibly.
      </p>
    </div>
  );
}
