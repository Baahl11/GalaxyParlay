"use client";

export type MarketCategory =
  | "goals"
  | "corners"
  | "cards"
  | "shots"
  | "offsides"
  | "all";

interface CategoryFilterProps {
  selectedCategories: MarketCategory[];
  onCategoryChange: (categories: MarketCategory[]) => void;
  totalCount?: number;
}

const CATEGORIES = [
  {
    key: "all" as MarketCategory,
    label: "All Markets",
    icon: "🎯",
    color: "purple",
  },
  {
    key: "goals" as MarketCategory,
    label: "Goals",
    icon: "⚽",
    color: "green",
  },
  {
    key: "corners" as MarketCategory,
    label: "Corners",
    icon: "🚩",
    color: "yellow",
  },
  { key: "cards" as MarketCategory, label: "Cards", icon: "🟨", color: "red" },
  { key: "shots" as MarketCategory, label: "Shots", icon: "🎯", color: "blue" },
  {
    key: "offsides" as MarketCategory,
    label: "Offsides",
    icon: "🚫",
    color: "orange",
  },
];

const COLOR_CLASSES = {
  purple:
    "bg-purple-500/20 text-purple-400 border-purple-500/50 hover:bg-purple-500/30",
  green:
    "bg-green-500/20 text-green-400 border-green-500/50 hover:bg-green-500/30",
  yellow:
    "bg-yellow-500/20 text-yellow-400 border-yellow-500/50 hover:bg-yellow-500/30",
  red: "bg-red-500/20 text-red-400 border-red-500/50 hover:bg-red-500/30",
  blue: "bg-blue-500/20 text-blue-400 border-blue-500/50 hover:bg-blue-500/30",
  orange:
    "bg-orange-500/20 text-orange-400 border-orange-500/50 hover:bg-orange-500/30",
};

const ACTIVE_COLOR_CLASSES = {
  purple: "bg-purple-500 text-white border-purple-500",
  green: "bg-green-500 text-white border-green-500",
  yellow: "bg-yellow-500 text-white border-yellow-500",
  red: "bg-red-500 text-white border-red-500",
  blue: "bg-blue-500 text-white border-blue-500",
  orange: "bg-orange-500 text-white border-orange-500",
};

export function CategoryFilter({
  selectedCategories,
  onCategoryChange,
  totalCount = 0,
}: CategoryFilterProps) {
  const isAllSelected = selectedCategories.includes("all");

  const handleToggle = (category: MarketCategory) => {
    if (category === "all") {
      // Toggle all
      onCategoryChange(isAllSelected ? [] : ["all"]);
    } else {
      // Toggle specific category
      if (isAllSelected) {
        // If "all" is selected, switch to just this category
        onCategoryChange([category]);
      } else {
        const newSelection = selectedCategories.includes(category)
          ? selectedCategories.filter((c) => c !== category)
          : [...selectedCategories, category];

        // If all specific categories are selected, switch to "all"
        const specificCategories = CATEGORIES.filter(
          (c) => c.key !== "all",
        ).map((c) => c.key);
        const allSpecificSelected = specificCategories.every((c) =>
          newSelection.includes(c),
        );

        onCategoryChange(allSpecificSelected ? ["all"] : newSelection);
      }
    }
  };

  const isActive = (category: MarketCategory) => {
    return isAllSelected || selectedCategories.includes(category);
  };

  return (
    <div className="bg-gray-900/50 rounded-xl p-4 border border-gray-700/50">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-sm font-semibold text-gray-400">
          Filter by Category:
        </span>
      </div>

      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map(({ key, label, icon, color }) => {
          const active = isActive(key);
          const baseClasses =
            "px-4 py-2 rounded-lg border transition-all duration-200 flex items-center gap-2 text-sm font-medium cursor-pointer";
          const colorClasses = active
            ? ACTIVE_COLOR_CLASSES[color as keyof typeof ACTIVE_COLOR_CLASSES]
            : COLOR_CLASSES[color as keyof typeof COLOR_CLASSES];

          return (
            <button
              key={key}
              onClick={() => handleToggle(key)}
              className={`${baseClasses} ${colorClasses}`}
            >
              <span>{icon}</span>
              <span>{label}</span>
              {key !== "all" && active && !isAllSelected && (
                <svg
                  className="w-4 h-4"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
            </button>
          );
        })}
      </div>

      {!isAllSelected && selectedCategories.length > 0 && (
        <div className="mt-3 text-xs text-gray-500">
          Showing {selectedCategories.length} categor
          {selectedCategories.length === 1 ? "y" : "ies"}
        </div>
      )}
    </div>
  );
}
