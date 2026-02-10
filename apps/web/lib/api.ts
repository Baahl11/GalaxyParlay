// ParlayGalaxy API Client

import type {
  Fixture,
  FixturesResponse,
  League,
  MultiMarketPrediction,
  StatsResponse,
  TopPlayersResponse,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "https://galaxyparlay-production.up.railway.app";

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
  const searchParams = new URLSearchParams();

  if (params?.league_id)
    searchParams.set("league_id", params.league_id.toString());
  if (params?.status) searchParams.set("status", params.status);
  if (params?.date_from) searchParams.set("date_from", params.date_from);
  if (params?.date_to) searchParams.set("date_to", params.date_to);
  if (params?.limit) searchParams.set("limit", params.limit.toString());

  const url = `${API_BASE_URL}/api/fixtures?${searchParams.toString()}`;
  const response = await fetch(url, { next: { revalidate: 60 } });

  if (!response.ok) {
    throw new Error(`Failed to fetch fixtures: ${response.statusText}`);
  }

  const data: FixturesResponse = await response.json();
  return data.fixtures || data.data || [];
}

/**
 * Fetch a single fixture by ID
 */
export async function getFixture(id: number): Promise<Fixture> {
  const response = await fetch(`${API_BASE_URL}/api/fixtures/${id}`, {
    next: { revalidate: 60 },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch fixture: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch active leagues
 */
export async function getLeagues(): Promise<League[]> {
  const response = await fetch(`${API_BASE_URL}/api/leagues`, {
    next: { revalidate: 300 },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch leagues: ${response.statusText}`);
  }

  const data = await response.json();
  return data.data;
}

/**
 * Fetch platform statistics
 */
export async function getStats(): Promise<StatsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/stats`, {
    next: { revalidate: 120 },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch stats: ${response.statusText}`);
  }

  return response.json();
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
 * Fetch multi-market predictions for a fixture
 */
export async function getMultiMarketPrediction(
  fixtureId: number,
): Promise<MultiMarketPrediction> {
  const response = await fetch(
    `${API_BASE_URL}/api/multi-market-prediction/${fixtureId}`,
    {
      next: { revalidate: 120 },
    },
  );

  if (!response.ok) {
    throw new Error(
      `Failed to fetch multi-market prediction: ${response.statusText}`,
    );
  }

  return response.json();
}

/**
 * Fetch top scorers
 */
export async function getTopScorers(params?: {
  limit?: number;
  min_goals?: number;
}): Promise<TopPlayersResponse> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set("limit", params.limit.toString());
  if (params?.min_goals)
    searchParams.set("min_goals", params.min_goals.toString());

  const response = await fetch(
    `${API_BASE_URL}/jobs/top-scorers?${searchParams.toString()}`,
    {
      next: { revalidate: 300 },
    },
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch top scorers: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch top shooters
 */
export async function getTopShooters(params?: {
  limit?: number;
  min_shots?: number;
}): Promise<TopPlayersResponse> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set("limit", params.limit.toString());
  if (params?.min_shots)
    searchParams.set("min_shots", params.min_shots.toString());

  const response = await fetch(
    `${API_BASE_URL}/jobs/top-shooters?${searchParams.toString()}`,
    {
      next: { revalidate: 300 },
    },
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch top shooters: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch value bets
 */
export async function getValueBets(params?: {
  min_edge?: number;
  min_ev?: number;
  limit?: number;
}): Promise<{ bets: ValueBet[]; summary: ValueBetSummary }> {
  const searchParams = new URLSearchParams();
  if (params?.min_edge)
    searchParams.set("min_edge", params.min_edge.toString());
  if (params?.min_ev) searchParams.set("min_ev", params.min_ev.toString());
  if (params?.limit) searchParams.set("limit", params.limit.toString());

  const response = await fetch(
    `${API_BASE_URL}/api/value-bets?${searchParams.toString()}`,
    {
      next: { revalidate: 60 },
    },
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch value bets: ${response.statusText}`);
  }

  return response.json();
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
