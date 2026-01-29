'use client';

import type { QualityGrade } from '@/lib/types';

interface QualityIndicatorProps {
  grade: QualityGrade;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

const gradeConfig: Record<QualityGrade, { bg: string; text: string; label: string; description: string }> = {
  A: {
    bg: 'bg-emerald-500',
    text: 'text-white',
    label: 'Excellent',
    description: 'High confidence prediction with strong data coverage',
  },
  B: {
    bg: 'bg-green-500',
    text: 'text-white',
    label: 'Good',
    description: 'Reliable prediction with good historical accuracy',
  },
  C: {
    bg: 'bg-yellow-500',
    text: 'text-black',
    label: 'Fair',
    description: 'Moderate confidence, use with caution',
  },
  D: {
    bg: 'bg-orange-500',
    text: 'text-white',
    label: 'Low',
    description: 'Limited data or lower model confidence',
  },
  F: {
    bg: 'bg-red-500',
    text: 'text-white',
    label: 'Poor',
    description: 'Insufficient data for reliable prediction',
  },
};

const sizeClasses = {
  sm: 'w-5 h-5 text-xs',
  md: 'w-7 h-7 text-sm',
  lg: 'w-9 h-9 text-base',
};

export function QualityIndicator({ grade, size = 'md', showLabel = false }: QualityIndicatorProps) {
  const config = gradeConfig[grade];

  return (
    <div className="flex items-center gap-2" title={config.description}>
      <div
        className={`
          ${sizeClasses[size]} 
          ${config.bg} 
          ${config.text}
          rounded-full 
          flex items-center justify-center 
          font-bold
          shadow-sm
        `}
      >
        {grade}
      </div>
      {showLabel && (
        <span className="text-sm text-gray-400">{config.label}</span>
      )}
    </div>
  );
}

interface QualityBarProps {
  score: number; // 0-1
  label?: string;
}

export function QualityBar({ score, label }: QualityBarProps) {
  const percentage = Math.round(score * 100);
  
  const getColor = (pct: number) => {
    if (pct >= 80) return 'bg-emerald-500';
    if (pct >= 60) return 'bg-green-500';
    if (pct >= 40) return 'bg-yellow-500';
    if (pct >= 20) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>{label}</span>
          <span>{percentage}%</span>
        </div>
      )}
      <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${getColor(percentage)} transition-all duration-300`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
