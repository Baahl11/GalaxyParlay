"use client";

// VERSION: 2026-02-10-BUILD-002 - DEBUGGING ENABLED
console.log('🚀 MatchDrawer.tsx LOADED - Version BUILD-002');

import { getMultiMarketPrediction } from "@/lib/api";
import type { Fixture, MultiMarketPrediction } from "@/lib/types";
import { LEAGUE_FLAGS, LEAGUE_NAMES } from "@/lib/types";
import { useEffect, useState } from "react";
import { AllMarketsView } from "./AllMarketsView";
import { CategoryFilter, type MarketCategory } from "./CategoryFilter";
import { GradeFilter } from "./GradeFilter";

interface MatchDrawerProps {
  fixture: Fixture | null;
  isOpen: boolean;
  onClose: () => void;
}

// Next.js false positive: functions are valid props in client components
// @ts-ignore
export function MatchDrawer({ fixture, isOpen, onClose }: MatchDrawerProps) {
  console.log('[MatchDrawer] 🔄 Component rendered with props:', { fixture: fixture?.id, isOpen });
  
  const [prediction, setPrediction] = useState<MultiMarketPrediction | null>(
    null,
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [selectedCategories, setSelectedCategories] = useState<
    MarketCategory[]
  >(["all"]);
  const [gradeAOnly, setGradeAOnly] = useState(false);
  const [profitableOnly, setProfitableOnly] = useState(false);

  useEffect(() => {
    console.log('[MatchDrawer] useEffect triggered:', { fixture: fixture?.id, isOpen });
    if (fixture && isOpen) {
      console.log('[MatchDrawer] 🚀 Calling loadPrediction...');
      loadPrediction();
    }
  }, [fixture?.id, isOpen]);

  const loadPrediction = async () => {
    if (!fixture) {
      console.log("[MatchDrawer] No fixture provided");
      return;
    }

    console.log(
      "[MatchDrawer] Loading multi-market prediction for fixture:",
      fixture.id,
    );
    console.log("[MatchDrawer] Fixture data:", {
      id: fixture.id,
      home: fixture.home_team_name,
      away: fixture.away_team_name,
    });

    setLoading(true);
    setError(null);

    try {
      const data = await getMultiMarketPrediction(fixture.id);
      console.log(
        "[MatchDrawer] ✅ Successfully loaded multi-market prediction:",
        data,
      );
      setPrediction(data);
    } catch (err) {
      console.error(
        "[MatchDrawer] ❌ Error loading multi-market prediction:",
        err,
      );
      const errorMessage =
        err instanceof Error ? err.message : "Failed to load predictions";
      console.error("[MatchDrawer] Error message:", errorMessage);
      setError(`[v2] ${errorMessage}`);
    } finally {
      setLoading(false);
      console.log("[MatchDrawer] Loading complete");
    }
  };

  if (!isOpen) return null;

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="fixed inset-y-0 right-0 w-full max-w-lg bg-gray-900 shadow-2xl z-50 overflow-y-auto border-l border-gray-700/50 transform transition-transform">
        {/* Header */}
        <div className="sticky top-0 bg-gray-900/95 backdrop-blur-sm border-b border-gray-700/50 p-4 z-10">
          <div className="flex items-center justify-between">
            <div>
              {fixture && (
                <span className="text-sm text-gray-400">
                  {LEAGUE_FLAGS[fixture.league_id] || "🏆"}{" "}
                  {LEAGUE_NAMES[fixture.league_id] || "League"}
                </span>
              )}
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-700/50 rounded-full transition-colors"
            >
              <svg
                className="w-5 h-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {fixture && (
            <div className="mt-3">
              <div className="flex items-center justify-between text-xl font-bold text-white">
                <span>{fixture.home_team_name}</span>
                <span className="text-gray-500">vs</span>
                <span className="text-right">{fixture.away_team_name}</span>
              </div>
              <div className="text-center text-sm text-gray-500 mt-1">
                {formatDate(fixture.kickoff_time)}
              </div>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="p-4">
          {loading && (
            <div className="flex flex-col items-center justify-center py-16">
              <div className="relative w-16 h-16">
                <div className="absolute inset-0 rounded-full border-4 border-purple-500/20"></div>
                <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-purple-500 animate-spin"></div>
              </div>
              <p className="text-gray-500 mt-4">Analyzing match...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4 text-center">
              <p className="text-red-400">{error}</p>
              <button
                onClick={loadPrediction}
                className="mt-3 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors"
              >
                Retry
              </button>
            </div>
          )}

          {prediction && !loading && (
            <div className="space-y-6">
              {/* Filters */}
              <div className="space-y-4">
                <CategoryFilter
                  selectedCategories={selectedCategories}
                  onCategoryChange={setSelectedCategories}
                  totalCount={
                    Object.keys(transformPredictionsToArray(prediction)).length
                  }
                />
                <GradeFilter
                  gradeAOnly={gradeAOnly}
                  profitableOnly={profitableOnly}
                  onGradeAChange={setGradeAOnly}
                  onProfitableChange={setProfitableOnly}
                  stats={getFilterStats(prediction)}
                />
              </div>

              {/* All Markets View */}
              <AllMarketsView
                predictions={transformPredictionsToArray(prediction)}
                selectedCategories={selectedCategories}
                gradeAOnly={gradeAOnly}
                profitableOnly={profitableOnly}
              />

              {/* Quality Score */}
              <div className="bg-gray-800/60 rounded-xl p-4 border border-gray-700/50">
                <h3 className="text-sm font-semibold text-gray-400 mb-3">
                  Overall Quality
                </h3>
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-2xl font-bold text-purple-400">
                      {prediction.quality_score?.toFixed(2) || "N/A"}
                    </div>
                    <div className="text-xs text-gray-500">Quality Score</div>
                  </div>
                  <div
                    className={`px-3 py-1 rounded-full text-sm font-bold ${
                      (prediction.quality_score || 0) >= 0.7
                        ? "bg-green-500/20 text-green-400"
                        : (prediction.quality_score || 0) >= 0.5
                          ? "bg-yellow-500/20 text-yellow-400"
                          : "bg-orange-500/20 text-orange-400"
                    }`}
                  >
                    {(prediction.quality_score || 0) >= 0.7
                      ? "✅ High"
                      : (prediction.quality_score || 0) >= 0.5
                        ? "⚠️ Medium"
                        : "🔶 Low"}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

// Helper functions to transform API data
function transformPredictionsToArray(prediction: MultiMarketPrediction) {
  const predictions = [];
  const preds = prediction.predictions;

  // Over/Under Goals
  for (const [key, value] of Object.entries(preds.over_under)) {
    if (typeof value === "object" && "over" in value && "under" in value) {
      const overProb = value.over ?? 0;
      const underProb = value.under ?? 0;
      const outcome = overProb > underProb ? "over" : "under";
      const confidence = Math.max(overProb, underProb);

      predictions.push({
        fixture_id: prediction.fixture_id,
        market_key: key, // Use full key: "over_under_0_5", "over_under_1_5", etc.
        prediction: { over: overProb, under: underProb },
        confidence_score: confidence,
        quality_grade: getGrade(confidence),
      });
    }
  }

  // Home/Away Goals
  for (const [key, value] of Object.entries(preds.team_goals || {})) {
    if (typeof value === "object" && "over" in value && "under" in value) {
      const overProb = value.over ?? 0;
      const underProb = value.under ?? 0;
      const confidence = Math.max(overProb, underProb);

      predictions.push({
        fixture_id: prediction.fixture_id,
        market_key: key,
        prediction: { over: overProb, under: underProb },
        confidence_score: confidence,
        quality_grade: getGrade(confidence),
      });
    }
  }

  // BTTS
  predictions.push({
    fixture_id: prediction.fixture_id,
    market_key: "both_teams_score",
    prediction: { yes: preds.btts.yes, no: preds.btts.no },
    confidence_score: Math.max(preds.btts.yes, preds.btts.no),
    quality_grade: getGrade(Math.max(preds.btts.yes, preds.btts.no)),
  });

  // First Half O/U
  if (preds.over_under.first_half_0_5) {
    const fh = preds.over_under.first_half_0_5;
    predictions.push({
      fixture_id: prediction.fixture_id,
      market_key: "first_half_over_under_0_5",
      prediction: { over: fh.over, under: fh.under },
      confidence_score: Math.max(fh.over, fh.under),
      quality_grade: getGrade(Math.max(fh.over, fh.under)),
    });
  }

  // Corners
  if (preds.corners) {
    for (const [key, value] of Object.entries(preds.corners)) {
      if (
        key.includes("over_") &&
        typeof value === "object" &&
        "over" in value &&
        "under" in value
      ) {
        const overProb = value.over ?? 0;
        const underProb = value.under ?? 0;
        const confidence = Math.max(overProb, underProb);

        predictions.push({
          fixture_id: prediction.fixture_id,
          market_key: `corners_${key}`,
          prediction: { over: overProb, under: underProb },
          confidence_score: confidence,
          quality_grade: getGrade(confidence),
        });
      }
    }
  }

  // Cards
  if (preds.cards) {
    for (const [key, value] of Object.entries(preds.cards)) {
      if (
        key.includes("over_") &&
        typeof value === "object" &&
        "over" in value &&
        "under" in value
      ) {
        const overProb = value.over ?? 0;
        const underProb = value.under ?? 0;
        const confidence = Math.max(overProb, underProb);

        predictions.push({
          fixture_id: prediction.fixture_id,
          market_key: `cards_${key}`,
          prediction: { over: overProb, under: underProb },
          confidence_score: confidence,
          quality_grade: getGrade(confidence),
        });
      }
    }
  }

  // Shots
  if (preds.shots) {
    for (const [key, value] of Object.entries(preds.shots)) {
      if (
        key.includes("over_") &&
        typeof value === "object" &&
        "over" in value &&
        "under" in value
      ) {
        const overProb = value.over ?? 0;
        const underProb = value.under ?? 0;
        const confidence = Math.max(overProb, underProb);

        predictions.push({
          fixture_id: prediction.fixture_id,
          market_key: `shots_on_target_${key}`,
          prediction: { over: overProb, under: underProb },
          confidence_score: confidence,
          quality_grade: getGrade(confidence),
        });
      }
    }
  }

  return predictions;
}

function getGrade(confidence: number): string {
  if (confidence >= 0.75) return "A";
  if (confidence >= 0.65) return "B";
  if (confidence >= 0.55) return "C";
  return "D";
}

function getFilterStats(prediction: MultiMarketPrediction) {
  const predictions = transformPredictionsToArray(prediction);
  return {
    total: predictions.length,
    gradeA: predictions.filter((p) => p.quality_grade === "A").length,
    profitable: predictions.filter((p) => p.confidence_score >= 0.6).length,
  };
}

function BestPickItem({
  label,
  probability,
}: {
  label: string;
  probability: number;
}) {
  return (
    <div className="flex items-center justify-between bg-gray-800/40 rounded-lg px-3 py-2">
      <span className="text-sm text-white">{label}</span>
      <span
        className={`text-sm font-bold ${
          probability >= 0.7
            ? "text-green-400"
            : probability >= 0.5
              ? "text-yellow-400"
              : "text-orange-400"
        }`}
      >
        {(probability * 100).toFixed(1)}%
      </span>
    </div>
  );
}
