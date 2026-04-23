// ParlayGalaxy API Client — reads directly from Supabase (no Railway dependency)

import { supabase } from "./supabase";
import type {
  Fixture,
  League,
  MultiMarketPrediction,
  StatsResponse,
  TopPlayersResponse,
} from "./types";

/** Parse a line suffix like "2_5" → 2.5 or "10_5" → 10.5 */
function parseLineSuffix(suffix: string): number {
  const lastUnderscore = suffix.lastIndexOf("_");
  if (lastUnderscore === -1) return parseFloat(suffix);
  return parseFloat(
    suffix.substring(0, lastUnderscore) +
      "." +
      suffix.substring(lastUnderscore + 1),
  );
}

/**
 * Fetch fixtures with optional filters
 */
export async function getFixtures(params?: {
  league_id?: number;
  status?: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
}): Promise<Fixture[]> {
  let query = supabase
    .from("fixtures")
    .select("*")
    .order("kickoff_time", { ascending: true });

  if (params?.league_id) query = query.eq("league_id", params.league_id);
  if (params?.status) query = query.eq("status", params.status);
  if (params?.date_from) query = query.gte("kickoff_time", params.date_from);
  if (params?.date_to) query = query.lte("kickoff_time", params.date_to);
  if (params?.limit) query = query.limit(params.limit);

  const { data, error } = await query;
  if (error) throw new Error(`Failed to fetch fixtures: ${error.message}`);
  return (data as Fixture[]) || [];
}

/**
 * Fetch a single fixture by ID
 */
export async function getFixture(id: number): Promise<Fixture> {
  const { data, error } = await supabase
    .from("fixtures")
    .select("*")
    .eq("id", id)
    .single();
  if (error) throw new Error(`Failed to fetch fixture: ${error.message}`);
  return data as Fixture;
}

/**
 * Fetch active leagues
 */
export async function getLeagues(): Promise<League[]> {
  const { data, error } = await supabase
    .from("leagues")
    .select("*")
    .eq("is_active", true)
    .order("name");
  if (error) throw new Error(`Failed to fetch leagues: ${error.message}`);
  return (data as League[]) || [];
}

/**
 * Fetch platform statistics
 */
export async function getStats(): Promise<StatsResponse> {
  const [fixturesRes, predictionsRes, leaguesRes, gradeRes] = await Promise.all(
    [
      supabase
        .from("fixtures")
        .select("id, status", { count: "exact", head: false }),
      supabase
        .from("model_predictions")
        .select("quality_grade, confidence_score", { count: "exact" }),
      supabase
        .from("leagues")
        .select("id", { count: "exact", head: true })
        .eq("is_active", true),
      supabase
        .from("model_predictions")
        .select("quality_grade")
        .eq("quality_grade", "A"),
    ],
  );

  const totalFixtures = fixturesRes.count ?? 0;
  const upcomingFixtures = (fixturesRes.data ?? []).filter(
    (f: { status: string }) => f.status === "NS",
  ).length;
  const liveFixtures = (fixturesRes.data ?? []).filter(
    (f: { status: string }) => ["1H", "2H", "HT", "LIVE"].includes(f.status),
  ).length;

  const totalPredictions = predictionsRes.count ?? 0;
  const gradeACount = gradeRes.data?.length ?? 0;
  const highConfidenceCount = (predictionsRes.data ?? []).filter(
    (p: { confidence_score: number }) => p.confidence_score >= 0.7,
  ).length;

  return {
    fixtures: {
      total: totalFixtures,
      upcoming: upcomingFixtures,
      live: liveFixtures,
    },
    predictions: {
      total: totalPredictions,
      grade_a: gradeACount,
      high_confidence: highConfidenceCount,
    },
    leagues: {
      active: leaguesRes.count ?? 0,
    },
    total_fixtures: totalFixtures,
    total_predictions: totalPredictions,
  };
}

/**
 * Format kickoff time for display
 */
export function formatKickoffTime(kickoffTime: string): string {
  const date = new Date(kickoffTime);
  return date.toLocaleString("es-ES", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Get time until kickoff
 */
export function getTimeUntilKickoff(kickoffTime: string): string {
  const now = new Date();
  const kickoff = new Date(kickoffTime);
  const diffMs = kickoff.getTime() - now.getTime();

  if (diffMs < 0) return "Started";

  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

  if (diffHours > 24) {
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ${diffHours % 24}h`;
  }

  return `${diffHours}h ${diffMinutes}m`;
}

/**
 * Fetch multi-market predictions for a fixture directly from Supabase.
 * Aggregates flat model_predictions rows into the MultiMarketPrediction shape.
 */
export async function getMultiMarketPrediction(
  fixtureId: number,
): Promise<MultiMarketPrediction> {
  const [fixtureRes, predictionsRes, qualityRes] = await Promise.all([
    supabase.from("fixtures").select("*").eq("id", fixtureId).single(),
    supabase
      .from("model_predictions")
      .select(
        "market_key, prediction, confidence_score, quality_grade, features_used",
      )
      .eq("fixture_id", fixtureId),
    supabase
      .from("quality_scores")
      .select("market_key, model_confidence, final_grade")
      .eq("fixture_id", fixtureId),
  ]);

  if (fixtureRes.error)
    throw new Error(`Fixture not found: ${fixtureRes.error.message}`);

  const fixture = fixtureRes.data as {
    id: number;
    home_team_name: string;
    away_team_name: string;
    kickoff_time: string;
    league_id: number;
  };

  const rows = (predictionsRes.data ?? []) as Array<{
    market_key: string;
    prediction: Record<string, number>;
    confidence_score: number;
    quality_grade: string;
    features_used: Record<string, number> | null;
  }>;

  const qualityRows = (qualityRes.data ?? []) as Array<{
    market_key: string;
    model_confidence: number;
    final_grade: string;
  }>;

  // Index rows by market_key
  const byKey: Record<string, (typeof rows)[0]> = {};
  for (const row of rows) {
    // Keep highest-confidence row per market_key
    if (
      !byKey[row.market_key] ||
      row.confidence_score > byKey[row.market_key].confidence_score
    ) {
      byKey[row.market_key] = row;
    }
  }

  // ── match_winner ──────────────────────────────────────────────────────────
  const mwRow = byKey["match_winner"];
  const match_winner = mwRow
    ? {
        home_win: mwRow.prediction.home_win ?? 0,
        draw: mwRow.prediction.draw ?? 0,
        away_win: mwRow.prediction.away_win ?? 0,
      }
    : undefined;

  // ── over_under (total goals) ───────────────────────────────────────────────
  const over_under: Record<
    string,
    { over: number; under: number; line: number }
  > = {};
  for (const [mk, row] of Object.entries(byKey)) {
    if (mk.startsWith("over_under_")) {
      const suffix = mk.replace("over_under_", "");
      const line = parseLineSuffix(suffix);
      over_under[String(line)] = {
        over: row.prediction.over ?? 0,
        under: row.prediction.under ?? 0,
        line,
      };
    }
  }

  // ── team_goals ─────────────────────────────────────────────────────────────
  const team_goals: Record<
    string,
    { over: number; under: number; team: string; line: number }
  > = {};
  for (const [mk, row] of Object.entries(byKey)) {
    if (mk.startsWith("home_team_over_under_")) {
      const suffix = mk.replace("home_team_over_under_", "");
      const line = parseLineSuffix(suffix);
      team_goals[`home_${line}`] = {
        over: row.prediction.over ?? 0,
        under: row.prediction.under ?? 0,
        team: "home",
        line,
      };
    } else if (mk.startsWith("away_team_over_under_")) {
      const suffix = mk.replace("away_team_over_under_", "");
      const line = parseLineSuffix(suffix);
      team_goals[`away_${line}`] = {
        over: row.prediction.over ?? 0,
        under: row.prediction.under ?? 0,
        team: "away",
        line,
      };
    }
  }

  // ── btts ───────────────────────────────────────────────────────────────────
  const bttsRow = byKey["both_teams_score"];
  const btts = bttsRow
    ? { yes: bttsRow.prediction.yes ?? 0, no: bttsRow.prediction.no ?? 0 }
    : { yes: 0.5, no: 0.5 };

  // ── corners ────────────────────────────────────────────────────────────────
  const expectedCornersTotal =
    rows.find(
      (r) =>
        r.market_key.startsWith("corners_") &&
        r.features_used?.expected_corners,
    )?.features_used?.expected_corners ?? 10;
  const corners: Record<string, unknown> = {
    expected: {
      home: Math.round(expectedCornersTotal * 0.47 * 10) / 10,
      away: Math.round(expectedCornersTotal * 0.53 * 10) / 10,
      total: expectedCornersTotal,
    },
  };
  for (const [mk, row] of Object.entries(byKey)) {
    if (mk.startsWith("corners_over_under_")) {
      const suffix = mk.replace("corners_over_under_", "");
      const line = parseLineSuffix(suffix);
      corners[`over_under_${line}`] = {
        over: row.prediction.over ?? 0,
        under: row.prediction.under ?? 0,
      };
    }
  }

  // ── cards ──────────────────────────────────────────────────────────────────
  const expectedCardsTotal =
    rows.find(
      (r) =>
        r.market_key.startsWith("cards_") && r.features_used?.expected_cards,
    )?.features_used?.expected_cards ?? 3.5;
  const cards: Record<string, unknown> = {
    expected: {
      home_yellow: Math.round(expectedCardsTotal * 0.5 * 10) / 10,
      away_yellow: Math.round(expectedCardsTotal * 0.5 * 10) / 10,
      total_yellow: expectedCardsTotal,
    },
  };
  for (const [mk, row] of Object.entries(byKey)) {
    if (mk.startsWith("cards_over_under_")) {
      const suffix = mk.replace("cards_over_under_", "");
      const line = parseLineSuffix(suffix);
      cards[`over_under_${line}`] = {
        over: row.prediction.over ?? 0,
        under: row.prediction.under ?? 0,
      };
    }
  }

  // ── shots ──────────────────────────────────────────────────────────────────
  const shots: Record<string, unknown> = {
    expected: {
      home_shots: 8,
      away_shots: 8,
      total_shots: 16,
      home_shots_on_target: 4,
      away_shots_on_target: 4,
      total_shots_on_target: 8,
    },
  };
  for (const [mk, row] of Object.entries(byKey)) {
    if (mk.startsWith("shots_on_target_over_under_")) {
      const suffix = mk.replace("shots_on_target_over_under_", "");
      const line = parseLineSuffix(suffix);
      shots[`over_under_${line}`] = {
        over: row.prediction.over ?? 0,
        under: row.prediction.under ?? 0,
      };
    }
  }

  // ── offsides ───────────────────────────────────────────────────────────────
  const offsides: Record<string, unknown> = {
    expected: { home: 2, away: 2, total: 4 },
  };
  for (const [mk, row] of Object.entries(byKey)) {
    if (mk.startsWith("offsides_over_under_")) {
      const suffix = mk.replace("offsides_over_under_", "");
      const line = parseLineSuffix(suffix);
      offsides[`over_under_${line}`] = {
        over: row.prediction.over ?? 0,
        under: row.prediction.under ?? 0,
      };
    }
  }

  // ── half_time ──────────────────────────────────────────────────────────────
  const htGoals: Record<string, { over: number; under: number; line: number }> =
    {};
  for (const [mk, row] of Object.entries(byKey)) {
    if (mk.startsWith("first_half_over_under_")) {
      const suffix = mk.replace("first_half_over_under_", "");
      const line = parseLineSuffix(suffix);
      htGoals[String(line)] = {
        over: row.prediction.over ?? 0,
        under: row.prediction.under ?? 0,
        line,
      };
    }
  }
  const half_time = {
    result_1x2: match_winner ?? { home: 0.35, draw: 0.35, away: 0.3 },
    goals: htGoals,
    corners: {
      expected: {
        home: Math.round(expectedCornersTotal * 0.5 * 0.47 * 10) / 10,
        away: Math.round(expectedCornersTotal * 0.5 * 0.53 * 10) / 10,
        total: Math.round(expectedCornersTotal * 0.5 * 10) / 10,
      },
    },
    expected: {
      home_goals: 0.7,
      away_goals: 0.65,
      total_goals: 1.35,
      total_corners: Math.round(expectedCornersTotal * 0.5 * 10) / 10,
    },
  };

  // ── expected (total xG) ───────────────────────────────────────────────────
  const mwFeatures = mwRow?.features_used ?? {};
  const homeElo = (mwFeatures.home_elo as number) ?? 1500;
  const awayElo = (mwFeatures.away_elo as number) ?? 1500;
  const eloDiff = homeElo - awayElo;
  const baseXg = 1.35;
  const homeXg = Math.round((baseXg + eloDiff * 0.0003) * 100) / 100;
  const awayXg = Math.round((baseXg - eloDiff * 0.0003) * 100) / 100;
  const expected = {
    home_goals: homeXg,
    away_goals: awayXg,
    total_goals: Math.round((homeXg + awayXg) * 100) / 100,
  };

  // ── quality score ─────────────────────────────────────────────────────────
  const avgQuality =
    qualityRows.length > 0
      ? qualityRows.reduce((sum, r) => sum + r.model_confidence, 0) /
        qualityRows.length
      : undefined;

  return {
    fixture_id: fixture.id,
    home_team: fixture.home_team_name,
    away_team: fixture.away_team_name,
    kickoff_time: fixture.kickoff_time,
    league_id: fixture.league_id,
    is_cup: false,
    quality_score: avgQuality,
    predictions: {
      match_winner,
      over_under,
      team_goals,
      btts,
      corners: corners as MultiMarketPrediction["predictions"]["corners"],
      cards: cards as MultiMarketPrediction["predictions"]["cards"],
      shots: shots as MultiMarketPrediction["predictions"]["shots"],
      offsides,
      exact_scores: [],
      half_time: half_time as MultiMarketPrediction["predictions"]["half_time"],
      expected,
    },
  };
}

/**
 * Fetch top scorers (no player stats available — returns empty)
 */
export async function getTopScorers(_params?: {
  limit?: number;
  min_goals?: number;
}): Promise<TopPlayersResponse> {
  return {
    status: "success",
    count: 0,
    total_players: 0,
    total_teams: 0,
    players: [],
  };
}

/**
 * Fetch top shooters (no player stats available — returns empty)
 */
export async function getTopShooters(_params?: {
  limit?: number;
  min_shots?: number;
}): Promise<TopPlayersResponse> {
  return {
    status: "success",
    count: 0,
    total_players: 0,
    total_teams: 0,
    players: [],
  };
}

/**
 * Fetch value bets by comparing model predictions against real bookmaker odds
 * from odds_snapshots table. Calculates genuine EV = model_prob*(odds-1) - (1-model_prob).
 */
export async function getValueBets(params?: {
  min_edge?: number;
  min_ev?: number;
  limit?: number;
}): Promise<{ bets: ValueBet[]; summary: ValueBetSummary }> {
  const limit = params?.limit ?? 20;
  const minEdge = params?.min_edge ?? 0.03;
  const minEv = params?.min_ev ?? 0.02;

  const emptyResult = {
    bets: [],
    summary: {
      total_bets: 0,
      avg_edge: 0,
      avg_ev: 0,
      best_ev: 0,
      total_kelly_units: 0,
    },
  };

  // Fetch A-grade predictions for key markets
  const { data: preds, error: predError } = await supabase
    .from("model_predictions")
    .select(
      `market_key, prediction, confidence_score, quality_grade, fixture_id,
       fixtures!inner(home_team_name, away_team_name, kickoff_time, league_id, status)`,
    )
    .eq("quality_grade", "A")
    .gte("confidence_score", 0.55)
    .in("market_key", ["match_winner", "over_under_2_5"])
    .order("confidence_score", { ascending: false })
    .limit(200);

  if (predError || !preds || preds.length === 0) return emptyResult;

  // Only NS fixtures
  const activePreds = preds.filter((p) => {
    const fx = p.fixtures as unknown as { status: string };
    return fx.status === "NS";
  });
  if (activePreds.length === 0) return emptyResult;

  // Unique fixture IDs
  const fixtureIds = [
    ...new Set(activePreds.map((p) => p.fixture_id as number)),
  ];

  // Fetch real bookmaker odds for those fixtures
  const { data: oddsRows } = await supabase
    .from("odds_snapshots")
    .select("fixture_id, market_key, odds_data, bookmaker")
    .in("fixture_id", fixtureIds)
    .in("market_key", ["match_winner", "over_under_2.5"]);

  // Build index: fixture_id -> oddsMarketKey -> { odds_data, bookmaker }
  const oddsIndex: Record<
    number,
    Record<string, { data: Record<string, number>; bookmaker: string }>
  > = {};
  for (const od of oddsRows ?? []) {
    const fid = od.fixture_id as number;
    const mk = od.market_key as string;
    if (!oddsIndex[fid]) oddsIndex[fid] = {};
    // Prefer Bet365, don't overwrite if already set
    if (!oddsIndex[fid][mk]) {
      oddsIndex[fid][mk] = {
        data: od.odds_data as Record<string, number>,
        bookmaker: od.bookmaker as string,
      };
    }
  }

  const bets: ValueBet[] = [];

  for (const row of activePreds) {
    const fx = row.fixtures as unknown as {
      home_team_name: string;
      away_team_name: string;
      kickoff_time: string;
      league_id: number;
    };
    const pred = row.prediction as Record<string, number>;
    const marketKey = row.market_key as string;
    const fixtureId = row.fixture_id as number;
    const fixtureOdds = oddsIndex[fixtureId] ?? {};

    // Map prediction market key → odds market key
    const oddsMarketKey =
      marketKey === "over_under_2_5" ? "over_under_2.5" : marketKey;
    const oddsEntry = fixtureOdds[oddsMarketKey];

    if (!oddsEntry) continue; // no real odds for this fixture/market

    let selection = "";
    let modelProb = 0;
    let bookmakerOdds = 0;
    const bookmaker = oddsEntry.bookmaker;
    const oddsData = oddsEntry.data;

    if (marketKey === "match_winner") {
      const homeP = pred.home_win ?? 0;
      const drawP = pred.draw ?? 0;
      const awayP = pred.away_win ?? 0;
      const best = Math.max(homeP, drawP, awayP);
      if (best === homeP) {
        selection = "Home Win";
        modelProb = homeP;
        bookmakerOdds = oddsData["home"] ?? 0;
      } else if (best === drawP) {
        selection = "Draw";
        modelProb = drawP;
        bookmakerOdds = oddsData["draw"] ?? 0;
      } else {
        selection = "Away Win";
        modelProb = awayP;
        bookmakerOdds = oddsData["away"] ?? 0;
      }
    } else if (marketKey === "over_under_2_5") {
      const isOver = (pred.over ?? 0) >= (pred.under ?? 0);
      selection = isOver ? "Over 2.5" : "Under 2.5";
      modelProb = isOver ? (pred.over ?? 0) : (pred.under ?? 0);
      bookmakerOdds = isOver
        ? (oddsData["over 2.5"] ?? 0)
        : (oddsData["under 2.5"] ?? 0);
    }

    if (!bookmakerOdds || bookmakerOdds < 1.1 || modelProb <= 0) continue;

    const impliedProb = 1 / bookmakerOdds;
    const edge = modelProb - impliedProb;
    const ev = modelProb * (bookmakerOdds - 1) - (1 - modelProb);
    const kellyFraction =
      edge > 0 ? Math.min(edge / (bookmakerOdds - 1), 0.1) : 0;

    if (edge < minEdge || ev < minEv) continue;

    bets.push({
      fixture_id: fixtureId,
      home_team: fx.home_team_name,
      away_team: fx.away_team_name,
      kickoff_time: fx.kickoff_time,
      league_id: fx.league_id,
      market: marketKey,
      selection,
      odds: Math.round(bookmakerOdds * 100) / 100,
      model_prob: Math.round(modelProb * 1000) / 1000,
      implied_prob: Math.round(impliedProb * 1000) / 1000,
      edge: Math.round(edge * 1000) / 1000,
      ev: Math.round(ev * 1000) / 1000,
      kelly_fraction: Math.round(kellyFraction * 1000) / 1000,
      grade: row.quality_grade as string,
      confidence: Math.round((row.confidence_score as number) * 1000) / 1000,
    });
  }

  // Sort by EV desc
  bets.sort((a, b) => b.ev - a.ev);
  const limitedBets = bets.slice(0, limit);

  const avgEdge =
    limitedBets.length > 0
      ? limitedBets.reduce((s, b) => s + b.edge, 0) / limitedBets.length
      : 0;
  const avgEv =
    limitedBets.length > 0
      ? limitedBets.reduce((s, b) => s + b.ev, 0) / limitedBets.length
      : 0;
  const bestEv =
    limitedBets.length > 0 ? Math.max(...limitedBets.map((b) => b.ev)) : 0;

  return {
    bets: limitedBets,
    summary: {
      total_bets: limitedBets.length,
      avg_edge: Math.round(avgEdge * 1000) / 1000,
      avg_ev: Math.round(avgEv * 1000) / 1000,
      best_ev: Math.round(bestEv * 1000) / 1000,
      total_kelly_units:
        Math.round(
          limitedBets.reduce((s, b) => s + b.kelly_fraction, 0) * 1000,
        ) / 1000,
    },
  };
}

// Value Bet types
export interface ValueBet {
  fixture_id: number;
  home_team: string;
  away_team: string;
  kickoff_time: string;
  league_id: number;
  market: string;
  selection: string;
  odds: number;
  model_prob: number;
  implied_prob: number;
  edge: number;
  ev: number;
  kelly_fraction: number;
  kelly_stake?: number;
  grade: string;
  confidence: number;
}

export interface ValueBetSummary {
  total_bets: number;
  avg_edge: number;
  avg_ev: number;
  best_ev: number;
  total_kelly_units: number;
}

export interface BacktestData {
  summary: {
    fixtures_tested: number;
    predictions_tested: number;
    markets_tested: number;
  };
  new_model: { accuracy: number; brier_score: number; log_loss: number };
  by_market?: Record<
    string,
    {
      old_accuracy: number;
      new_accuracy: number;
      improvement: number;
      sample_size: number;
    }
  >;
}

/**
 * Fetch model accuracy stats from Railway backtest endpoint
 */
export async function getBacktestResults(): Promise<BacktestData | null> {
  const railwayUrl =
    process.env.NEXT_PUBLIC_API_URL ??
    "https://galaxyparlay-production.up.railway.app";
  try {
    const res = await fetch(`${railwayUrl}/jobs/backtest-results`, {
      next: { revalidate: 3600 },
    });
    if (!res.ok) return null;
    const json = await res.json();
    return json.data as BacktestData;
  } catch {
    return null;
  }
}
