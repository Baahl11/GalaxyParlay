"use client";

interface GradeFilterProps {
  gradeAOnly: boolean;
  profitableOnly: boolean;
  onGradeAChange: (enabled: boolean) => void;
  onProfitableChange: (enabled: boolean) => void;
  stats?: {
    total: number;
    gradeA: number;
    profitable: number;
  };
}

export function GradeFilter({
  gradeAOnly,
  profitableOnly,
  onGradeAChange,
  onProfitableChange,
  stats,
}: GradeFilterProps) {
  return (
    <div className="bg-gray-900/50 rounded-xl p-4 border border-gray-700/50">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-sm font-semibold text-gray-400">
          Quality Filters:
        </span>
      </div>

      <div className="space-y-3">
        {/* Grade A Only Toggle */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => onGradeAChange(!gradeAOnly)}
              className={`
                relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                ${gradeAOnly ? "bg-green-500" : "bg-gray-700"}
              `}
            >
              <span
                className={`
                  inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                  ${gradeAOnly ? "translate-x-6" : "translate-x-1"}
                `}
              />
            </button>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-white">
                  Grade A Only
                </span>
                <span className="px-2 py-0.5 bg-green-500/20 text-green-400 text-xs font-bold rounded">
                  A
                </span>
              </div>
              <div className="text-xs text-gray-500 mt-0.5">
                ≥75% confidence • 63-70% accuracy
              </div>
            </div>
          </div>
          {stats && (
            <div className="text-right">
              <div className="text-lg font-bold text-green-400">
                {stats.gradeA}
              </div>
              <div className="text-xs text-gray-500">predictions</div>
            </div>
          )}
        </div>

        {/* Profitable Only Toggle */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => onProfitableChange(!profitableOnly)}
              className={`
                relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                ${profitableOnly ? "bg-purple-500" : "bg-gray-700"}
              `}
            >
              <span
                className={`
                  inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                  ${profitableOnly ? "translate-x-6" : "translate-x-1"}
                `}
              />
            </button>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-white">
                  Profitable Only
                </span>
                <span className="px-2 py-0.5 bg-purple-500/20 text-purple-400 text-xs font-bold rounded">
                  💎
                </span>
              </div>
              <div className="text-xs text-gray-500 mt-0.5">
                ≥60% accuracy • Positive ROI expected
              </div>
            </div>
          </div>
          {stats && (
            <div className="text-right">
              <div className="text-lg font-bold text-purple-400">
                {stats.profitable}
              </div>
              <div className="text-xs text-gray-500">predictions</div>
            </div>
          )}
        </div>
      </div>

      {/* Active Filters Info */}
      {(gradeAOnly || profitableOnly) && (
        <div className="mt-4 p-3 bg-gray-800/50 rounded-lg border border-gray-700/30">
          <div className="flex items-start gap-2">
            <svg
              className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                clipRule="evenodd"
              />
            </svg>
            <div>
              <div className="text-xs font-medium text-blue-400 mb-1">
                Active Filters
              </div>
              <div className="text-xs text-gray-400">
                {gradeAOnly &&
                  profitableOnly &&
                  "Showing only Grade A predictions with positive ROI"}
                {gradeAOnly &&
                  !profitableOnly &&
                  "Showing only Grade A predictions (≥75% confidence)"}
                {!gradeAOnly &&
                  profitableOnly &&
                  "Showing only predictions with ≥60% accuracy"}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
