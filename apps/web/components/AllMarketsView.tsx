"use client";

import { useMemo } from "react";
import type { MarketCategory } from "./CategoryFilter";

interface Prediction {
  fixture_id: number;
  market_key: string;
  prediction: any;
  confidence_score: number;
  quality_grade: string;
}

interface AllMarketsViewProps {
  predictions: Prediction[];
  selectedCategories: MarketCategory[];
  gradeAOnly: boolean;
  profitableOnly: boolean;
}

// Market categorization - includes both old and new key formats
const MARKET_CATEGORIES = {
  goals: [
    "match_winner",
    "both_teams_score",
    "over_under_0_5",
    "over_under_1_5",
    "over_under_2_5",
    "over_under_3_5",
    "over_under_4_5",
    "over_under_5_5",
    "home_over_0_5",
    "home_over_1_5",
    "home_over_2_5",
    "away_over_0_5",
    "away_over_1_5",
    "away_over_2_5",
    "first_half_over_under_0_5",
  ],
  corners: [
    // New backend keys (total_over_X_5)
    "corners_total_over_7_5",
    "corners_total_over_8_5",
    "corners_total_over_9_5",
    "corners_total_over_10_5",
    "corners_total_over_11_5",
    "corners_total_over_12_5",
    // Home/Away corners
    "corners_home_over_3_5",
    "corners_home_over_4_5",
    "corners_home_over_5_5",
    "corners_away_over_3_5",
    "corners_away_over_4_5",
    "corners_away_over_5_5",
    // Old format (for backwards compat)
    "corners_over_under_7_5",
    "corners_over_under_8_5",
    "corners_over_under_9_5",
    "corners_over_under_10_5",
    "corners_over_under_11_5",
    "corners_over_under_12_5",
  ],
  cards: [
    // New backend keys (total_over_X_5)
    "cards_total_over_2_5",
    "cards_total_over_3_5",
    "cards_total_over_4_5",
    "cards_total_over_5_5",
    "cards_total_over_6_5",
    // Old format
    "cards_over_under_2_5",
    "cards_over_under_3_5",
    "cards_over_under_4_5",
    "cards_over_under_5_5",
    "cards_over_under_6_5",
  ],
  shots: [
    // New backend keys (sot_over_X_5)
    "shots_sot_over_6_5",
    "shots_sot_over_7_5",
    "shots_sot_over_8_5",
    "shots_sot_over_9_5",
    "shots_sot_over_10_5",
    "shots_sot_over_11_5",
    // Old format
    "shots_on_target_over_under_6_5",
    "shots_on_target_over_under_7_5",
    "shots_on_target_over_under_8_5",
    "shots_on_target_over_under_9_5",
    "shots_on_target_over_under_10_5",
  ],
  offsides: [
    // New backend keys (total_over_X_5)
    "offsides_total_over_3_5",
    "offsides_total_over_4_5",
    "offsides_total_over_5_5",
    "offsides_total_over_6_5",
    // Home/Away offsides
    "offsides_home_over_1_5",
    "offsides_home_over_2_5",
    "offsides_home_over_3_5",
    "offsides_away_over_1_5",
    "offsides_away_over_2_5",
    "offsides_away_over_3_5",
    // Old format
    "offsides_over_under_3_5",
    "offsides_over_under_4_5",
    "offsides_over_under_5_5",
    "offsides_over_under_6_5",
  ],
};

const MARKET_LABELS: Record<string, string> = {
  match_winner: "Match Winner",
  both_teams_score: "Both Teams Score",
  over_under_0_5: "Over/Under 0.5",
  over_under_1_5: "Over/Under 1.5",
  over_under_2_5: "Over/Under 2.5",
  over_under_3_5: "Over/Under 3.5",
  over_under_4_5: "Over/Under 4.5",
  over_under_5_5: "Over/Under 5.5",
  home_over_0_5: "Home Over 0.5",
  home_over_1_5: "Home Over 1.5",
  home_over_2_5: "Home Over 2.5",
  away_over_0_5: "Away Over 0.5",
  away_over_1_5: "Away Over 1.5",
  away_over_2_5: "Away Over 2.5",
  first_half_over_under_0_5: "First Half O/U 0.5",
  // Corners - new format
  corners_total_over_7_5: "Corners O/U 7.5",
  corners_total_over_8_5: "Corners O/U 8.5",
  corners_total_over_9_5: "Corners O/U 9.5",
  corners_total_over_10_5: "Corners O/U 10.5",
  corners_total_over_11_5: "Corners O/U 11.5",
  corners_total_over_12_5: "Corners O/U 12.5",
  corners_home_over_3_5: "Home Corners O/U 3.5",
  corners_home_over_4_5: "Home Corners O/U 4.5",
  corners_home_over_5_5: "Home Corners O/U 5.5",
  corners_away_over_3_5: "Away Corners O/U 3.5",
  corners_away_over_4_5: "Away Corners O/U 4.5",
  corners_away_over_5_5: "Away Corners O/U 5.5",
  // Old format
  corners_over_under_7_5: "Corners O/U 7.5",
  corners_over_under_8_5: "Corners O/U 8.5",
  corners_over_under_9_5: "Corners O/U 9.5",
  corners_over_under_10_5: "Corners O/U 10.5",
  corners_over_under_11_5: "Corners O/U 11.5",
  corners_over_under_12_5: "Corners O/U 12.5",
  // Cards - new format
  cards_total_over_2_5: "Cards O/U 2.5",
  cards_total_over_3_5: "Cards O/U 3.5",
  cards_total_over_4_5: "Cards O/U 4.5",
  cards_total_over_5_5: "Cards O/U 5.5",
  cards_total_over_6_5: "Cards O/U 6.5",
  // Old format
  cards_over_under_2_5: "Cards O/U 2.5",
  cards_over_under_3_5: "Cards O/U 3.5",
  cards_over_under_4_5: "Cards O/U 4.5",
  cards_over_under_5_5: "Cards O/U 5.5",
  cards_over_under_6_5: "Cards O/U 6.5",
  // Shots - new format
  shots_sot_over_6_5: "Shots OT O/U 6.5",
  shots_sot_over_7_5: "Shots OT O/U 7.5",
  shots_sot_over_8_5: "Shots OT O/U 8.5",
  shots_sot_over_9_5: "Shots OT O/U 9.5",
  shots_sot_over_10_5: "Shots OT O/U 10.5",
  shots_sot_over_11_5: "Shots OT O/U 11.5",
  // Old format
  shots_on_target_over_under_6_5: "Shots O/U 6.5",
  shots_on_target_over_under_7_5: "Shots O/U 7.5",
  shots_on_target_over_under_8_5: "Shots O/U 8.5",
  shots_on_target_over_under_9_5: "Shots O/U 9.5",
  shots_on_target_over_under_10_5: "Shots O/U 10.5",
  // Offsides - new format
  offsides_total_over_3_5: "Offsides O/U 3.5",
  offsides_total_over_4_5: "Offsides O/U 4.5",
  offsides_total_over_5_5: "Offsides O/U 5.5",
  offsides_total_over_6_5: "Offsides O/U 6.5",
  offsides_home_over_1_5: "Home Offsides O/U 1.5",
  offsides_home_over_2_5: "Home Offsides O/U 2.5",
  offsides_home_over_3_5: "Home Offsides O/U 3.5",
  offsides_away_over_1_5: "Away Offsides O/U 1.5",
  offsides_away_over_2_5: "Away Offsides O/U 2.5",
  offsides_away_over_3_5: "Away Offsides O/U 3.5",
  // Old format
  offsides_over_under_3_5: "Offsides O/U 3.5",
  offsides_over_under_4_5: "Offsides O/U 4.5",
  offsides_over_under_5_5: "Offsides O/U 5.5",
  offsides_over_under_6_5: "Offsides O/U 6.5",
};

const CATEGORY_ICONS = {
  goals: "⚽",
  corners: "🚩",
  cards: "🟨",
  shots: "🎯",
  offsides: "🚫",
};

const CATEGORY_COLORS = {
  goals: "green",
  corners: "yellow",
  cards: "red",
  shots: "blue",
  offsides: "orange",
};

const GRADE_COLORS = {
  A: "bg-green-500/20 text-green-400 border-green-500/50",
  B: "bg-blue-500/20 text-blue-400 border-blue-500/50",
  C: "bg-yellow-500/20 text-yellow-400 border-yellow-500/50",
  D: "bg-orange-500/20 text-orange-400 border-orange-500/50",
};

function getCategoryForMarket(marketKey: string): MarketCategory | null {
  // First check explicit list
  for (const [category, markets] of Object.entries(MARKET_CATEGORIES)) {
    if (markets.includes(marketKey)) {
      return category as MarketCategory;
    }
  }

  // Pattern matching for dynamic keys
  if (marketKey.startsWith("corners_")) return "corners";
  if (marketKey.startsWith("cards_")) return "cards";
  if (marketKey.startsWith("shots_")) return "shots";
  if (marketKey.startsWith("offsides_")) return "offsides";
  if (
    marketKey.includes("over_under") ||
    marketKey.includes("btts") ||
    marketKey.includes("home_over") ||
    marketKey.includes("away_over")
  )
    return "goals";

  return null;
}

// Generate label from market key if not in map
function getMarketLabel(marketKey: string): string {
  if (MARKET_LABELS[marketKey]) return MARKET_LABELS[marketKey];

  // Parse key to generate human-readable label
  // e.g., "corners_total_over_9_5" -> "Corners O/U 9.5"
  const parts = marketKey.split("_");
  const category = parts[0].charAt(0).toUpperCase() + parts[0].slice(1);

  if (marketKey.includes("_over_")) {
    const lineMatch = marketKey.match(/(\d+)_(\d+)$/);
    if (lineMatch) {
      const line = `${lineMatch[1]}.${lineMatch[2]}`;
      if (marketKey.includes("home_")) return `Home ${category} O/U ${line}`;
      if (marketKey.includes("away_")) return `Away ${category} O/U ${line}`;
      return `${category} O/U ${line}`;
    }
  }

  return marketKey.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
}

function MarketPredictionCard({ prediction }: { prediction: Prediction }) {
  const category = getCategoryForMarket(prediction.market_key);
  const label = getMarketLabel(prediction.market_key);
  const icon =
    category && category !== "all"
      ? CATEGORY_ICONS[category as keyof typeof CATEGORY_ICONS]
      : "🎯";
  const color =
    category && category !== "all"
      ? CATEGORY_COLORS[category as keyof typeof CATEGORY_COLORS]
      : "purple";

  // Get best outcome
  const predictionData = prediction.prediction;
  let bestOutcome = "";
  let bestProb = 0;

  if (typeof predictionData === "object" && predictionData !== null) {
    Object.entries(predictionData).forEach(([key, value]) => {
      if (typeof value === "number" && value > bestProb) {
        bestOutcome = key;
        bestProb = value;
      }
    });
  }

  const gradeColorClass =
    GRADE_COLORS[prediction.quality_grade as keyof typeof GRADE_COLORS] ||
    GRADE_COLORS.D;

  return (
    <div className="bg-gray-800/40 rounded-lg p-3 border border-gray-700/50 hover:border-purple-500/50 transition-all">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-lg">{icon}</span>
          <span className="text-sm font-medium text-white">{label}</span>
        </div>
        <div
          className={`px-2 py-0.5 rounded text-xs font-bold border ${gradeColorClass}`}
        >
          {prediction.quality_grade}
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-400 capitalize">
          {bestOutcome.replace("_", " ")}
        </div>
        <div className="text-lg font-bold text-purple-400">
          {(bestProb * 100).toFixed(1)}%
        </div>
      </div>

      {/* Confidence bar */}
      <div className="mt-2 h-1.5 bg-gray-700/50 rounded-full overflow-hidden">
        <div
          className={`h-full bg-gradient-to-r ${
            bestProb >= 0.75
              ? "from-green-500 to-green-400"
              : bestProb >= 0.65
                ? "from-blue-500 to-blue-400"
                : bestProb >= 0.55
                  ? "from-yellow-500 to-yellow-400"
                  : "from-orange-500 to-orange-400"
          }`}
          style={{ width: `${bestProb * 100}%` }}
        />
      </div>

      {/* FIFA Badge if high confidence */}
      {bestProb >= 0.7 && (
        <div className="mt-2 flex items-center gap-1 text-xs text-purple-400">
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
          <span>FIFA Enhanced</span>
        </div>
      )}
    </div>
  );
}

export function AllMarketsView({
  predictions,
  selectedCategories,
  gradeAOnly,
  profitableOnly,
}: AllMarketsViewProps) {
  const filteredPredictions = useMemo(() => {
    return predictions.filter((pred) => {
      // Filter by category
      const category = getCategoryForMarket(pred.market_key);
      if (!selectedCategories.includes("all")) {
        if (!category || !selectedCategories.includes(category)) {
          return false;
        }
      }

      // Filter by grade
      if (gradeAOnly && pred.quality_grade !== "A") {
        return false;
      }

      // Filter by profitability (≥60% accuracy threshold)
      if (profitableOnly && pred.confidence_score < 0.6) {
        return false;
      }

      return true;
    });
  }, [predictions, selectedCategories, gradeAOnly, profitableOnly]);

  // Group by category
  const groupedPredictions = useMemo(() => {
    const groups: Record<string, Prediction[]> = {
      goals: [],
      corners: [],
      cards: [],
      shots: [],
      offsides: [],
    };

    filteredPredictions.forEach((pred) => {
      const category = getCategoryForMarket(pred.market_key);
      if (category && groups[category]) {
        groups[category].push(pred);
      }
    });

    return groups;
  }, [filteredPredictions]);

  const totalPredictions = filteredPredictions.length;
  const gradeACount = filteredPredictions.filter(
    (p) => p.quality_grade === "A",
  ).length;

  if (predictions.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No predictions available for this fixture</p>
      </div>
    );
  }

  if (filteredPredictions.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-4xl mb-3">🔍</div>
        <p className="text-gray-400 mb-2">No predictions match your filters</p>
        <p className="text-sm text-gray-500">
          Try adjusting the category or quality filters
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="bg-gray-800/30 rounded-lg p-4 border border-gray-700/50">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-white">
              {totalPredictions}
            </div>
            <div className="text-xs text-gray-500">Total Markets</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-green-400">
              {gradeACount}
            </div>
            <div className="text-xs text-gray-500">Grade A</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-purple-400">
              {
                filteredPredictions.filter((p) => p.confidence_score >= 0.6)
                  .length
              }
            </div>
            <div className="text-xs text-gray-500">Profitable</div>
          </div>
        </div>
      </div>

      {/* Grouped Predictions */}
      {Object.entries(groupedPredictions).map(([category, categoryPreds]) => {
        if (categoryPreds.length === 0) return null;

        return (
          <div key={category} className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-xl">
                {CATEGORY_ICONS[category as keyof typeof CATEGORY_ICONS]}
              </span>
              <h3 className="text-lg font-bold text-white capitalize">
                {category}
              </h3>
              <span className="px-2 py-0.5 bg-gray-700/50 text-gray-400 text-xs rounded-full">
                {categoryPreds.length}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {categoryPreds.map((pred) => (
                <MarketPredictionCard key={pred.market_key} prediction={pred} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
