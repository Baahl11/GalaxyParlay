'use client';

import type { Fixture } from '@/lib/types';
import { useState } from 'react';
import { FixtureCard } from './FixtureCard';

interface FixtureListProps {
  fixtures: Fixture[];
  title?: string;
  onFixtureClick?: (fixture: Fixture) => void;
}

export function FixtureList({ fixtures, title, onFixtureClick }: FixtureListProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const handleToggle = (id: number) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const handleClick = (fixture: Fixture) => {
    if (onFixtureClick) {
      onFixtureClick(fixture);
    }
  };

  if (!fixtures || !Array.isArray(fixtures) || fixtures.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">⚽</div>
        <h3 className="text-xl font-semibold text-gray-400 mb-2">No fixtures found</h3>
        <p className="text-gray-500">Check back later for upcoming matches</p>
      </div>
    );
  }

  return (
    <div>
      {title && (
        <h2 className="text-2xl font-bold text-white mb-6">{title}</h2>
      )}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {fixtures.map(fixture => (
          <FixtureCard
            key={fixture.id}
            fixture={fixture}
            expanded={expandedId === fixture.id}
            onToggle={() => handleToggle(fixture.id)}
            onClick={() => handleClick(fixture)}
          />
        ))}
      </div>
    </div>
  );
}
