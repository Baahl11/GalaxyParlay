# FASE 5 - Frontend Integration Plan

## Overview

This document outlines the steps to integrate FASE 5 Smart Parlay and Market Confidence features into the Next.js frontend.

---

## 1. API Client Updates

### Create Smart Parlay API Client

**File:** `apps/web/lib/api.ts`

```typescript
// Add to existing API functions

export interface ParlaySelection {
  fixture_id: number;
  market_key: string;
  selection: string;
  odds: number;
  predicted_prob?: number;
}

export interface ParlayValidationResponse {
  valid: boolean;
  reason: string;
  odds_penalty: number;
  original_odds: number;
  adjusted_odds: number;
  expected_value?: number;
  recommendation: string;
  details: {
    num_selections: number;
    fixtures: number[];
    markets: string[];
  };
}

export interface ParlayRecommendation {
  markets: string[];
  correlation: number;
  description: string;
  combined_odds: number;
  confidence: string;
}

export async function validateParlay(
  selections: ParlaySelection[],
): Promise<ParlayValidationResponse> {
  const response = await fetch(`${API_BASE_URL}/api/parlay/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ selections }),
  });

  if (!response.ok) throw new Error("Parlay validation failed");
  return response.json();
}

export async function getParlayRecommendations(
  fixtureId: number,
  maxSelections: number = 5,
): Promise<{
  fixture_id: number;
  home_team: string;
  away_team: string;
  recommendations: ParlayRecommendation[];
}> {
  const response = await fetch(
    `${API_BASE_URL}/api/parlay/recommendations/${fixtureId}?max_selections=${maxSelections}`,
  );

  if (!response.ok) throw new Error("Failed to get recommendations");
  return response.json();
}

export async function getCorrelationMatrix(): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/parlay/correlation-matrix`);
  if (!response.ok) throw new Error("Failed to get correlation matrix");
  return response.json();
}
```

---

## 2. UI Components

### A. Parlay Builder Component

**File:** `apps/web/components/ParlayBuilder.tsx`

```typescript
'use client';

import { useState, useEffect } from 'react';
import { validateParlay, type ParlaySelection } from '@/lib/api';

export function ParlayBuilder() {
  const [selections, setSelections] = useState<ParlaySelection[]>([]);
  const [validation, setValidation] = useState<any>(null);
  const [isValidating, setIsValidating] = useState(false);

  // Validate on selection change
  useEffect(() => {
    if (selections.length >= 2) {
      validateSelections();
    } else {
      setValidation(null);
    }
  }, [selections]);

  const validateSelections = async () => {
    setIsValidating(true);
    try {
      const result = await validateParlay(selections);
      setValidation(result);
    } catch (error) {
      console.error('Validation error:', error);
    } finally {
      setIsValidating(false);
    }
  };

  const addSelection = (selection: ParlaySelection) => {
    setSelections([...selections, selection]);
  };

  const removeSelection = (index: number) => {
    setSelections(selections.filter((_, i) => i !== index));
  };

  return (
    <div className="parlay-builder">
      <h2 className="text-2xl font-bold mb-4">Build Your Parlay</h2>

      {/* Selections List */}
      <div className="selections-list space-y-2 mb-4">
        {selections.map((sel, index) => (
          <div key={index} className="selection-item flex justify-between items-center p-3 bg-gray-100 rounded">
            <div>
              <span className="font-semibold">{sel.selection}</span>
              <span className="text-gray-600 text-sm ml-2">@ {sel.odds}</span>
            </div>
            <button
              onClick={() => removeSelection(index)}
              className="text-red-500 hover:text-red-700"
            >
              Remove
            </button>
          </div>
        ))}
      </div>

      {/* Validation Status */}
      {isValidating && (
        <div className="validation-loading p-4 bg-blue-50 rounded">
          Validating parlay...
        </div>
      )}

      {validation && (
        <div className={`validation-result p-4 rounded ${
          validation.valid ? 'bg-green-50' : 'bg-red-50'
        }`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-lg font-semibold">
              {validation.valid ? '✅' : '❌'} {validation.reason}
            </span>
            <span className={`text-sm px-2 py-1 rounded ${
              validation.recommendation === 'STRONG_VALUE' ? 'bg-green-500 text-white' :
              validation.recommendation === 'GOOD_VALUE' ? 'bg-blue-500 text-white' :
              validation.recommendation === 'NOT_RECOMMENDED' ? 'bg-red-500 text-white' :
              'bg-gray-500 text-white'
            }`}>
              {validation.recommendation.replace('_', ' ')}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4 mt-4">
            <div>
              <p className="text-sm text-gray-600">Original Odds</p>
              <p className="text-2xl font-bold">{validation.original_odds}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Adjusted Odds</p>
              <p className={`text-2xl font-bold ${
                validation.odds_penalty < 1 ? 'text-orange-500' : 'text-green-600'
              }`}>
                {validation.adjusted_odds}
              </p>
            </div>
          </div>

          {validation.expected_value !== null && (
            <div className="mt-4">
              <p className="text-sm text-gray-600">Expected Value (EV)</p>
              <p className={`text-xl font-bold ${
                validation.expected_value > 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {(validation.expected_value * 100).toFixed(2)}%
              </p>
            </div>
          )}

          {validation.odds_penalty < 1 && (
            <div className="mt-4 p-3 bg-orange-100 rounded">
              <p className="text-sm text-orange-800">
                ⚠️ Moderate correlation detected. Odds reduced by {((1 - validation.odds_penalty) * 100).toFixed(0)}%
              </p>
            </div>
          )}
        </div>
      )}

      {/* Place Bet Button */}
      {selections.length >= 2 && (
        <button
          disabled={!validation?.valid}
          className={`w-full mt-4 py-3 rounded font-semibold ${
            validation?.valid
              ? 'bg-green-500 text-white hover:bg-green-600'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          Place Parlay Bet
        </button>
      )}
    </div>
  );
}
```

### B. Smart Parlay Recommendations Widget

**File:** `apps/web/components/SmartParlayWidget.tsx`

```typescript
'use client';

import { useState, useEffect } from 'react';
import { getParlayRecommendations, type ParlayRecommendation } from '@/lib/api';

interface Props {
  fixtureId: number;
}

export function SmartParlayWidget({ fixtureId }: Props) {
  const [recommendations, setRecommendations] = useState<ParlayRecommendation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRecommendations();
  }, [fixtureId]);

  const loadRecommendations = async () => {
    try {
      const data = await getParlayRecommendations(fixtureId, 5);
      setRecommendations(data.recommendations);
    } catch (error) {
      console.error('Failed to load recommendations:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading smart parlays...</div>;
  if (recommendations.length === 0) return null;

  return (
    <div className="smart-parlay-widget bg-gradient-to-br from-purple-50 to-blue-50 p-6 rounded-lg">
      <h3 className="text-xl font-bold mb-4 flex items-center">
        <span className="mr-2">🧠</span>
        Smart Parlay Suggestions
      </h3>

      <div className="space-y-3">
        {recommendations.map((rec, index) => (
          <div
            key={index}
            className="parlay-card bg-white p-4 rounded-lg shadow hover:shadow-md transition"
          >
            <div className="flex justify-between items-start mb-2">
              <p className="font-semibold text-gray-800">{rec.description}</p>
              <span className={`text-xs px-2 py-1 rounded ${
                rec.confidence === 'HIGH' ? 'bg-green-100 text-green-800' :
                rec.confidence === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {rec.confidence}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <div className="text-sm text-gray-600">
                <span>Correlation: </span>
                <span className={`font-semibold ${
                  Math.abs(rec.correlation) < 0.3 ? 'text-green-600' : 'text-orange-600'
                }`}>
                  {(rec.correlation * 100).toFixed(1)}%
                </span>
              </div>

              <div className="text-right">
                <p className="text-2xl font-bold text-blue-600">
                  {rec.combined_odds.toFixed(2)}
                </p>
                <p className="text-xs text-gray-500">Combined Odds</p>
              </div>
            </div>

            <button className="mt-3 w-full py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition">
              Add to Bet Slip
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### C. Market Confidence Badge

**File:** `apps/web/components/MarketConfidenceBadge.tsx`

```typescript
interface Props {
  marketKey: string;
  accuracy?: number;
}

const MARKET_ACCURACY = {
  'over_under_1_5': 79.90,
  'match_winner_draw': 72.30,
  'over_under_2_5': 71.50,
  'over_under_3_5': 71.20,
  'both_teams_score': 70.10,
  'match_winner_away_win': 70.00,
  'match_winner_home_win': 61.70,
};

export function MarketConfidenceBadge({ marketKey, accuracy }: Props) {
  const acc = accuracy || MARKET_ACCURACY[marketKey as keyof typeof MARKET_ACCURACY];

  if (!acc) return null;

  const isPremium = acc >= 75;
  const isStandard = acc >= 65 && acc < 75;
  const isHidden = acc < 65;

  if (isHidden) {
    return (
      <span className="text-xs px-2 py-1 rounded bg-red-100 text-red-800">
        ⚠️ Low Confidence ({acc.toFixed(1)}%)
      </span>
    );
  }

  if (isPremium) {
    return (
      <span className="text-xs px-2 py-1 rounded bg-gradient-to-r from-yellow-400 to-orange-500 text-white font-semibold animate-pulse">
        ⭐ PREMIUM {acc.toFixed(1)}%
      </span>
    );
  }

  return (
    <span className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-800">
      📊 {acc.toFixed(1)}% Accuracy
    </span>
  );
}
```

---

## 3. Integration Steps

### Phase 1: API Layer (30 min)

1. ✅ Update `lib/api.ts` with new functions
2. ✅ Test API calls in browser console
3. ✅ Add TypeScript types

### Phase 2: Smart Parlay Builder (2 hours)

1. Create `ParlayBuilder.tsx` component
2. Implement real-time validation
3. Add selection management
4. Style validation warnings
5. Test with multiple selections

### Phase 3: Recommendations Widget (1 hour)

1. Create `SmartParlayWidget.tsx`
2. Fetch recommendations on fixture load
3. Display in sidebar or modal
4. Add "Add to Bet Slip" action

### Phase 4: Market Confidence (1 hour)

1. Create `MarketConfidenceBadge.tsx`
2. Add to prediction cards
3. Show Premium badge on Over/Under 1.5
4. Add tooltips with accuracy explanation

### Phase 5: Match Detail Integration (1 hour)

1. Update `MatchDrawer.tsx` or detail page
2. Add Smart Parlay Widget
3. Show market confidence on each prediction
4. Link to Parlay Builder

### Phase 6: Testing & Polish (1 hour)

1. Test all parlay scenarios
2. Test API error handling
3. Mobile responsiveness
4. Loading states
5. Empty states

---

## 4. UI/UX Considerations

### Visual Design

- **Premium Markets:** Gold/yellow gradient with star icon
- **Valid Parlays:** Green background with checkmark
- **Invalid Parlays:** Red background with warning
- **Moderate Correlation:** Orange/yellow warning

### User Flow

1. User browses match → sees predictions with confidence badges
2. Clicks "Build Parlay" → opens ParlayBuilder
3. Adds markets → sees real-time validation
4. Gets correlation warning if needed
5. Views Smart Parlay recommendations
6. Confirms bet with adjusted odds

### Messaging

- **High Correlation:** "⚠️ These markets are highly correlated. Combining them reduces value."
- **Moderate Correlation:** "⚠️ Moderate correlation detected. Odds adjusted by 5%."
- **Low Correlation:** "✅ Valid parlay combination. No correlation detected."
- **Premium Market:** "⭐ This market has 79.90% historical accuracy - our best performer!"

---

## 5. Testing Checklist

### Unit Tests

- [ ] Parlay validation with 2, 3, 4+ selections
- [ ] Correlation detection (high, moderate, low)
- [ ] Odds calculation and penalty application
- [ ] EV calculation with probabilities

### Integration Tests

- [ ] API calls with valid data
- [ ] API calls with invalid data (error handling)
- [ ] Loading states during API calls
- [ ] Empty states (no recommendations)

### User Acceptance Tests

- [ ] User can add/remove selections
- [ ] Validation updates in real-time
- [ ] Warnings are clear and understandable
- [ ] Recommendations are helpful
- [ ] Mobile experience is smooth

---

## 6. Performance Optimization

### Caching

- Cache correlation matrix (rarely changes)
- Cache market accuracy data
- Debounce validation API calls (300ms delay)

### Loading

- Show skeleton loaders during API calls
- Prefetch recommendations on hover
- Use optimistic UI updates

### Bundle Size

- Lazy load ParlayBuilder component
- Code split heavy validation logic
- Minimize icon/badge components

---

## 7. Analytics & Tracking

### Events to Track

```typescript
// Track parlay validation
analytics.track("parlay_validated", {
  num_selections: 3,
  is_valid: true,
  correlation_status: "low",
  expected_value: 0.042,
  recommendation: "GOOD_VALUE",
});

// Track parlay placement
analytics.track("parlay_placed", {
  num_selections: 3,
  original_odds: 5.92,
  adjusted_odds: 5.92,
  stake: 10,
});

// Track recommendation click
analytics.track("parlay_recommendation_clicked", {
  fixture_id: 123,
  markets: ["home_win", "over_1_5"],
  correlation: -0.021,
});
```

---

## 8. Deployment

### Environment Variables

```env
NEXT_PUBLIC_API_URL=https://your-worker.railway.app
```

### Build & Deploy

```bash
cd apps/web
npm run build
vercel deploy --prod
```

### Monitoring

- Monitor API response times
- Track validation success/failure rates
- Monitor user engagement with recommendations
- Track conversion rate on Smart Parlay bets

---

## 9. Documentation for Users

### Help Modal Content

```markdown
# Smart Parlay System

## What is Smart Parlay?

Our AI analyzes correlations between markets to protect you from bad parlays.

## How it works

1. **High Correlation (>70%)** - We reject the parlay
   Example: Over 2.5 + Over 3.5 (r=68.1%)

2. **Moderate Correlation (30-70%)** - We warn you and adjust odds
   Example: Over 2.5 + Over 1.5 (r=58.0%)

3. **Low Correlation (<30%)** - Approved parlay
   Example: Home Win + Over 1.5 (r=-2.1%)

## Why this matters

Combining correlated markets reduces your parlay value. Our system helps you find the best combinations.
```

---

## 10. Future Enhancements

### V2 Features

- [ ] Multi-fixture parlay optimization
- [ ] Parlay history and tracking
- [ ] Social parlay sharing
- [ ] Live parlay updates during matches
- [ ] Parlay insurance recommendations

### V3 Features

- [ ] AI-generated parlay explanations
- [ ] Personalized recommendations based on user history
- [ ] Parlay builder with drag-and-drop
- [ ] Advanced filters (max risk, target odds, etc.)

---

**Estimated Total Time:** 6-8 hours  
**Priority:** HIGH (key competitive advantage)  
**Complexity:** MEDIUM  
**Impact:** HIGH (user retention + differentiation)
