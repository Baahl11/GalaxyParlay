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
        height: 700,
        backgroundColor: 0x050510,
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
      const clusterRadius = 180;
      
      const clusters = [
        { grade: 'A', x: centerX - clusterRadius * 1.2, y: centerY - clusterRadius * 0.8, color: 0x22c55e, size: 14, glow: 0x22c55e },
        { grade: 'B', x: centerX + clusterRadius * 1.2, y: centerY - clusterRadius * 0.8, color: 0xfbbf24, size: 12, glow: 0xfbbf24 },
        { grade: 'C', x: centerX - clusterRadius * 0.6, y: centerY + clusterRadius, color: 0x9ca3af, size: 10, glow: 0x6b7280 },
        { grade: 'none', x: centerX + clusterRadius * 0.6, y: centerY + clusterRadius, color: 0x4b5563, size: 8, glow: 0x374151 },
      ];

      const nodes: FixtureNode[] = [];

      clusters.forEach(cluster => {
        const clusterFixtures = fixturesByQuality[cluster.grade];
        const count = clusterFixtures.length;
        if (count === 0) return;
        
        const radius = Math.min(180, 60 + count * 3);

        // Draw cluster background glow
        const clusterBg = new PIXI.Graphics();
        clusterBg.circle(0, 0, radius + 40);
        clusterBg.fill({ color: cluster.glow, alpha: 0.05 });
        clusterBg.x = cluster.x;
        clusterBg.y = cluster.y;
        nodesContainer.addChild(clusterBg);

        clusterFixtures.forEach((fixture, index) => {
          const angle = (index / count) * Math.PI * 2;
          const spread = radius * (0.6 + Math.random() * 0.4);
          const x = cluster.x + Math.cos(angle) * spread + (Math.random() - 0.5) * 30;
          const y = cluster.y + Math.sin(angle) * spread + (Math.random() - 0.5) * 30;

          // Create node with enhanced visuals
          const node = new PIXI.Graphics();
          
          // Outer glow ring
          node.circle(0, 0, cluster.size + 8);
          node.fill({ color: cluster.glow, alpha: 0.15 });
          
          // Middle glow
          node.circle(0, 0, cluster.size + 4);
          node.fill({ color: cluster.glow, alpha: 0.3 });
          
          // Inner bright circle
          node.circle(0, 0, cluster.size);
          node.fill({ color: cluster.color, alpha: 0.95 });
          
          // Core shine
          node.circle(cluster.size * 0.3, -cluster.size * 0.3, cluster.size * 0.4);
          node.fill({ color: 0xffffff, alpha: 0.4 });
          
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

          // Add interaction with better feedback
          node.on('pointerover', () => {
            setHoveredFixture(fixture);
            if (onFixtureHover) onFixtureHover(fixture);
            node.scale.set(1.8);
            node.alpha = 1;
            
            // Add pulsing glow on hover
            const hoverGlow = new PIXI.Graphics();
            hoverGlow.circle(0, 0, cluster.size + 12);
            hoverGlow.fill({ color: cluster.glow, alpha: 0.4 });
            node.addChild(hoverGlow);
          });

          node.on('pointerout', () => {
            setHoveredFixture(null);
            if (onFixtureHover) onFixtureHover(null);
            node.scale.set(1);
            node.alpha = 0.95;
            
            // Remove hover effects
            if (node.children.length > 0) {
              node.removeChildren();
              
              // Recreate base graphics
              node.circle(0, 0, cluster.size + 8);
              node.fill({ color: cluster.glow, alpha: 0.15 });
              node.circle(0, 0, cluster.size + 4);
              node.fill({ color: cluster.glow, alpha: 0.3 });
              node.circle(0, 0, cluster.size);
              node.fill({ color: cluster.color, alpha: 0.95 });
              node.circle(cluster.size * 0.3, -cluster.size * 0.3, cluster.size * 0.4);
              node.fill({ color: 0xffffff, alpha: 0.4 });
            }
          });

          node.on('pointertap', () => {
            if (onFixtureClick) {
              // Flash effect on click
              node.alpha = 1;
              node.scale.set(2);
              setTimeout(() => {
                node.scale.set(1);
              }, 150);
              onFixtureClick(fixture);
            }
          });

          nodesContainer.addChild(node);
        });
      });

      // Add cluster labels
      clusters.forEach(cluster => {
        if (fixturesByQuality[cluster.grade].length === 0) return;
        
        const label = new PIXI.Text({
          text: `Grade ${cluster.grade}\n${fixturesByQuality[cluster.grade].length} fixtures`,
          style: {
            fontFamily: 'Inter, system-ui, sans-serif',
            fontSize: 14,
            fontWeight: 'bold',
            fill: cluster.color,
            align: 'center',
          },
        });
        label.anchor.set(0.5);
        label.x = cluster.x;
        label.y = cluster.y - (Math.min(180, 60 + fixturesByQuality[cluster.grade].length * 3) + 60);
        label.alpha = 0.8;
        nodesContainer.addChild(label);
      });

      nodesRef.current = nodes;

      // Add background stars for atmosphere
      const starsContainer = new PIXI.Container();
      app.stage.addChildAt(starsContainer, 0);
      
      for (let i = 0; i < 100; i++) {
        const star = new PIXI.Graphics();
        const size = Math.random() * 2 + 0.5;
        star.circle(0, 0, size);
        star.fill({ color: 0xffffff, alpha: Math.random() * 0.5 + 0.2 });
        star.x = Math.random() * app.screen.width;
        star.y = Math.random() * app.screen.height;
        starsContainer.addChild(star);
      }

      // Enhanced animation loop
      let frame = 0;
      app.ticker.add(() => {
        frame++;
        
        // Animate fixture nodes
        nodes.forEach((node, index) => {
          // Gentle floating animation with unique phase
          const phase = index * 0.1;
          const floatY = Math.sin(frame * 0.015 + phase) * 3;
          const floatX = Math.cos(frame * 0.01 + phase) * 2;
          node.sprite.y = node.y + floatY;
          node.sprite.x = node.x + floatX;
          
          // Pulse alpha slightly
          const pulse = Math.sin(frame * 0.02 + phase) * 0.1 + 0.9;
          node.sprite.alpha = pulse;
        });
        
        // Twinkle background stars
        starsContainer.children.forEach((star, index) => {
          const twinkle = Math.sin(frame * 0.05 + index * 0.5) * 0.3 + 0.7;
          star.alpha = twinkle * 0.5;
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
          700
        );
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <div className="relative">
      <div ref={containerRef} className="w-full rounded-3xl overflow-hidden border-2 border-purple-500/30 shadow-2xl shadow-purple-500/10" />
      
      {/* Hover tooltip - Enhanced with all predictions */}
      {hoveredFixture && (
        <div className="absolute top-4 left-4 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 backdrop-blur-xl border-2 border-purple-500/50 rounded-2xl p-5 max-w-md pointer-events-none shadow-2xl shadow-purple-500/20">
          {/* Header */}
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="px-2 py-1 text-xs font-bold bg-purple-500/20 text-purple-300 rounded-lg border border-purple-500/30">
                {hoveredFixture.quality_scores?.find(q => q.market_key === 'match_winner')?.final_grade || 'N/A'}
              </span>
              <span className="text-xs text-gray-400">
                {new Date(hoveredFixture.kickoff_time).toLocaleDateString('en-US', { 
                  month: 'short', 
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </span>
            </div>
          </div>

          {/* Teams */}
          <div className="mb-4 pb-4 border-b border-gray-700">
            <div className="flex items-center justify-between mb-1">
              <div className="text-base font-bold text-white">{hoveredFixture.home_team_name}</div>
              {hoveredFixture.predictions?.find(p => p.market_key === 'match_winner') && (
                <div className="text-sm font-semibold text-green-400">
                  {(() => {
                    const pred = hoveredFixture.predictions.find(p => p.market_key === 'match_winner');
                    if (pred && typeof pred.prediction === 'object') {
                      return ((pred.prediction as any).home_win * 100).toFixed(0) + '%';
                    }
                    return '';
                  })()}
                </div>
              )}
            </div>
            <div className="text-xs text-gray-400 text-center my-1">vs</div>
            <div className="flex items-center justify-between">
              <div className="text-base font-bold text-white">{hoveredFixture.away_team_name}</div>
              {hoveredFixture.predictions?.find(p => p.market_key === 'match_winner') && (
                <div className="text-sm font-semibold text-red-400">
                  {(() => {
                    const pred = hoveredFixture.predictions.find(p => p.market_key === 'match_winner');
                    if (pred && typeof pred.prediction === 'object') {
                      return ((pred.prediction as any).away_win * 100).toFixed(0) + '%';
                    }
                    return '';
                  })()}
                </div>
              )}
            </div>
          </div>

          {/* All Market Predictions */}
          {hoveredFixture.predictions && hoveredFixture.predictions.length > 0 ? (
            <div className="space-y-2">
              <div className="text-xs font-semibold text-purple-300 mb-2">AI PREDICTIONS</div>
              {hoveredFixture.predictions.slice(0, 6).map((pred, idx) => {
                const quality = hoveredFixture.quality_scores?.find(q => q.market_key === pred.market_key);
                return (
                  <div key={idx} className="bg-gray-800/50 rounded-lg p-2">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-gray-300 uppercase">
                        {pred.market_key.replace(/_/g, ' ')}
                      </span>
                      {quality && (
                        <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${
                          quality.final_grade === 'A' ? 'bg-green-500/20 text-green-400' :
                          quality.final_grade === 'B' ? 'bg-amber-500/20 text-amber-400' :
                          'bg-gray-500/20 text-gray-400'
                        }`}>
                          {quality.final_grade}
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-purple-400 font-semibold">
                      {(() => {
                        if (typeof pred.prediction === 'object') {
                          const p = pred.prediction as any;
                          if (pred.market_key === 'match_winner') {
                            return `${(p.home_win * 100).toFixed(0)}% / ${(p.draw * 100).toFixed(0)}% / ${(p.away_win * 100).toFixed(0)}%`;
                          } else if (pred.market_key === 'both_teams_score') {
                            return `YES ${(p.yes * 100).toFixed(0)}% | NO ${(p.no * 100).toFixed(0)}%`;
                          } else if (pred.market_key.includes('over_under')) {
                            return `O ${(p.over * 100).toFixed(0)}% | U ${(p.under * 100).toFixed(0)}%`;
                          } else if (pred.market_key.includes('corners')) {
                            return `O ${(p.over * 100).toFixed(0)}% | U ${(p.under * 100).toFixed(0)}%`;
                          }
                        }
                        return JSON.stringify(pred.prediction);
                      })()}
                    </div>
                  </div>
                );
              })}
              {hoveredFixture.predictions.length > 6 && (
                <div className="text-xs text-gray-500 text-center pt-1">
                  +{hoveredFixture.predictions.length - 6} more markets • Click to see all
                </div>
              )}
            </div>
          ) : (
            <div className="text-xs text-gray-500 text-center py-2">No predictions available</div>
          )}
        </div>
      )}

      {/* Legend - Enhanced */}
      <div className="absolute bottom-4 right-4 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 backdrop-blur-xl border-2 border-gray-700/50 rounded-xl p-4 shadow-2xl">
        <div className="text-xs font-bold text-purple-300 mb-3 flex items-center gap-2">
          <span className="text-base">⭐</span>
          QUALITY GRADES
        </div>
        <div className="space-y-2.5">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-4 h-4 rounded-full bg-green-500 shadow-lg shadow-green-500/50" />
              <div className="absolute inset-0 w-4 h-4 rounded-full bg-green-500 animate-ping opacity-20" />
            </div>
            <div>
              <div className="text-xs font-semibold text-white">Grade A</div>
              <div className="text-[10px] text-gray-400">Highest Quality Picks</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-3.5 h-3.5 rounded-full bg-amber-500 shadow-lg shadow-amber-500/50" />
            </div>
            <div>
              <div className="text-xs font-semibold text-white">Grade B</div>
              <div className="text-[10px] text-gray-400">Good Quality Picks</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-gray-500 shadow-lg shadow-gray-500/30" />
            <div>
              <div className="text-xs font-semibold text-white">Grade C</div>
              <div className="text-[10px] text-gray-400">Lower Confidence</div>
            </div>
          </div>
        </div>
        <div className="mt-3 pt-3 border-t border-gray-700">
          <div className="text-[10px] text-gray-500 text-center">
            💡 Hover to preview • Click for details
          </div>
        </div>
      </div>
    </div>
  );
}
