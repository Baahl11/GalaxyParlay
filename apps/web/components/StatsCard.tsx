'use client';

import type { StatsResponse } from '@/lib/types';

interface StatsCardProps {
  stats: StatsResponse | null;
}

export function StatsCard({ stats }: StatsCardProps) {
  if (!stats) return null;
  
  // Support both new and legacy API formats
  const totalFixtures = stats.fixtures?.total ?? stats.total_fixtures ?? 0;
  const totalPredictions = stats.predictions?.total ?? stats.total_predictions ?? 0;
  const gradeA = stats.predictions?.grade_a ?? stats.grade_distribution?.A ?? 0;
  const highConfidence = stats.predictions?.high_confidence ?? stats.grade_distribution?.B ?? 0;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <StatItem 
        label="Total Fixtures" 
        value={totalFixtures.toString()}
        icon="📊"
      />
      <StatItem 
        label="Predictions" 
        value={totalPredictions.toString()}
        icon="🎯"
      />
      <StatItem 
        label="Grade A Picks" 
        value={gradeA.toString()}
        icon="⭐"
      />
      <StatItem 
        label="High Confidence" 
        value={highConfidence.toString()}
        icon="💪"
      />
    </div>
  );
}

interface StatItemProps {
  label: string;
  value: string;
  icon: string;
}

function StatItem({ label, value, icon }: StatItemProps) {
  return (
    <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/30">
      <div className="text-2xl mb-2">{icon}</div>
      <div className="text-2xl font-bold text-white mb-1">{value}</div>
      <div className="text-sm text-gray-400">{label}</div>
    </div>
  );
}
