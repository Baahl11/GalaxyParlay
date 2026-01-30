'use client';

import type { Fixture } from '@/lib/types';
import * as PIXI from 'pixi.js';
import { useEffect, useRef, useState } from 'react';

interface GalaxyCanvasProps {
  fixtures: Fixture[];
  onFixtureClick?: (fixture: Fixture) => void;
  onFixtureHover?: (fixture: Fixture | null) => void;
}

interface FixtureNode {
  fixture: Fixture;
  sprite: PIXI.Graphics;
  x: number;
  y: number;
  targetX: number;
  targetY: number;
  quality: string;
}

export function GalaxyCanvas({ fixtures, onFixtureClick, onFixtureHover }: GalaxyCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const appRef = useRef<PIXI.Application | null>(null);
  const nodesRef = useRef<FixtureNode[]>([]);
  const [hoveredFixture, setHoveredFixture] = useState<Fixture | null>(null);

  useEffect(() => {
    if (!containerRef.current || fixtures.length === 0) return;

    // Initialize PixiJS
    const app = new PIXI.Application();
    appRef.current = app;

    (async () => {
      await app.init({
        width: containerRef.current!.clientWidth,
        height: 600,
        backgroundColor: 0x0a0a0f,
        antialias: true,
        resolution: window.devicePixelRatio || 1,
        autoDensity: true,
      });

      containerRef.current!.appendChild(app.canvas);

      // Create container for nodes
      const nodesContainer = new PIXI.Container();
      app.stage.addChild(nodesContainer);

      // Enable interactivity
      nodesContainer.eventMode = 'static';
      nodesContainer.hitArea = app.screen;

      // Group fixtures by quality grade
      const fixturesByQuality: { [key: string]: Fixture[] } = {
        A: [],
        B: [],
        C: [],
        none: [],
      };

      fixtures.forEach(fixture => {
        const mainQuality = fixture.quality_scores?.find(q => q.market_key === 'match_winner');
        const grade = mainQuality?.final_grade || 'none';
        fixturesByQuality[grade].push(fixture);
      });

      // Create clusters - position nodes in circular clusters by quality
      const centerX = app.screen.width / 2;
      const centerY = app.screen.height / 2;
      const clusterRadius = 200;
      const clusters = [
        { grade: 'A', x: centerX, y: centerY - clusterRadius, color: 0x10b981, size: 12 },
        { grade: 'B', x: centerX - clusterRadius, y: centerY + clusterRadius / 2, color: 0xf59e0b, size: 10 },
        { grade: 'C', x: centerX + clusterRadius, y: centerY + clusterRadius / 2, color: 0x6b7280, size: 8 },
        { grade: 'none', x: centerX, y: centerY + clusterRadius, color: 0x374151, size: 6 },
      ];

      const nodes: FixtureNode[] = [];

      clusters.forEach(cluster => {
        const clusterFixtures = fixturesByQuality[cluster.grade];
        const count = clusterFixtures.length;
        const radius = Math.min(150, 50 + count * 5);

        clusterFixtures.forEach((fixture, index) => {
          const angle = (index / count) * Math.PI * 2;
          const spread = radius * (0.7 + Math.random() * 0.3);
          const x = cluster.x + Math.cos(angle) * spread + (Math.random() - 0.5) * 20;
          const y = cluster.y + Math.sin(angle) * spread + (Math.random() - 0.5) * 20;

          // Create node sprite
          const node = new PIXI.Graphics();
          
          // Outer glow
          node.circle(0, 0, cluster.size + 4);
          node.fill({ color: cluster.color, alpha: 0.2 });
          
          // Inner circle
          node.circle(0, 0, cluster.size);
          node.fill({ color: cluster.color, alpha: 0.8 });
          
          node.x = x;
          node.y = y;
          node.eventMode = 'static';
          node.cursor = 'pointer';

          // Store fixture data
          const fixtureNode: FixtureNode = {
            fixture,
            sprite: node,
            x,
            y,
            targetX: x,
            targetY: y,
            quality: cluster.grade,
          };

          nodes.push(fixtureNode);

          // Add interaction
          node.on('pointerover', () => {
            setHoveredFixture(fixture);
            if (onFixtureHover) onFixtureHover(fixture);
            node.scale.set(1.5);
            node.alpha = 1;
          });

          node.on('pointerout', () => {
            setHoveredFixture(null);
            if (onFixtureHover) onFixtureHover(null);
            node.scale.set(1);
            node.alpha = 0.8;
          });

          node.on('pointertap', () => {
            if (onFixtureClick) {
              onFixtureClick(fixture);
            }
          });

          nodesContainer.addChild(node);
        });
      });

      nodesRef.current = nodes;

      // Animation loop
      let frame = 0;
      app.ticker.add(() => {
        frame++;
        nodes.forEach(node => {
          // Gentle floating animation
          const floatY = Math.sin(frame * 0.02 + node.x * 0.01) * 2;
          node.sprite.y = node.y + floatY;
        });
      });
    })();

    // Cleanup
    return () => {
      if (appRef.current) {
        appRef.current.destroy(true, { children: true });
        appRef.current = null;
      }
    };
  }, [fixtures, onFixtureClick, onFixtureHover]);

  // Handle resize
  useEffect(() => {
    const handleResize = () => {
      if (appRef.current && containerRef.current) {
        appRef.current.renderer.resize(
          containerRef.current.clientWidth,
          600
        );
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <div className="relative">
      <div ref={containerRef} className="w-full rounded-2xl overflow-hidden border border-gray-800" />
      
      {/* Hover tooltip */}
      {hoveredFixture && (
        <div className="absolute top-4 left-4 bg-gray-900/95 backdrop-blur-sm border border-purple-500/30 rounded-lg p-4 max-w-sm pointer-events-none">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-medium text-purple-400">
              {hoveredFixture.quality_scores?.find(q => q.market_key === 'match_winner')?.final_grade || 'N/A'}
            </span>
            <span className="text-xs text-gray-500">
              {new Date(hoveredFixture.kickoff_time).toLocaleDateString()}
            </span>
          </div>
          <div className="space-y-1">
            <div className="text-sm font-semibold text-white">
              {hoveredFixture.home_team_name}
            </div>
            <div className="text-xs text-gray-400">vs</div>
            <div className="text-sm font-semibold text-white">
              {hoveredFixture.away_team_name}
            </div>
          </div>
          {hoveredFixture.predictions && hoveredFixture.predictions.length > 0 && (
            <div className="mt-2 pt-2 border-t border-gray-700">
              <div className="text-xs text-gray-400">Prediction</div>
              <div className="text-sm text-purple-400">
                {(() => {
                  const pred = hoveredFixture.predictions[0];
                  if (pred.market_key === 'match_winner' && typeof pred.prediction === 'object') {
                    const p = pred.prediction as any;
                    const homeWin = (p.home_win * 100).toFixed(0);
                    const draw = (p.draw * 100).toFixed(0);
                    const awayWin = (p.away_win * 100).toFixed(0);
                    return `${homeWin}% - ${draw}% - ${awayWin}%`;
                  }
                  return 'N/A';
                })()}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-4 right-4 bg-gray-900/95 backdrop-blur-sm border border-gray-800 rounded-lg p-3">
        <div className="text-xs font-semibold text-gray-400 mb-2">Quality Grades</div>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span className="text-xs text-gray-300">Grade A - High Quality</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            <span className="text-xs text-gray-300">Grade B - Medium Quality</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-gray-500" />
            <span className="text-xs text-gray-300">Grade C - Lower Quality</span>
          </div>
        </div>
      </div>
    </div>
  );
}
