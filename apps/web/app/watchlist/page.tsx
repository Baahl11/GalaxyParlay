"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getWatchlist, removeWatchlistItem, type WatchlistItem } from "@/lib/api";
import { supabase } from "@/lib/supabase";

export default function WatchlistPage() {
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);

      const { data } = await supabase.auth.getUser();
      if (!data.user) {
        setUserEmail(null);
        setItems([]);
        setLoading(false);
        return;
      }

      setUserEmail(data.user.email ?? null);
      const list = await getWatchlist();
      setItems(list);
      setLoading(false);
    };

    load();
  }, []);

  const handleRemove = async (watchlistId: string) => {
    setError(null);
    const result = await removeWatchlistItem(watchlistId);
    if (result.status === "error") {
      setError(result.message ?? "No se pudo eliminar");
      return;
    }
    setItems((prev) => prev.filter((item) => item.id !== watchlistId));
  };

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    setUserEmail(null);
    setItems([]);
  };

  return (
    <div className="min-h-screen px-4 py-12">
      <div className="mx-auto w-full max-w-3xl">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-display text-white">Watchlist</h1>
            <p className="mt-2 text-sm text-gray-400">
              Tus fixtures guardados para seguir en vivo.
            </p>
          </div>
          {userEmail && (
            <button
              onClick={handleSignOut}
              className="px-4 py-2 rounded-full border border-gray-600 text-gray-200 text-xs hover:bg-gray-800/60"
            >
              Cerrar sesion
            </button>
          )}
        </div>

        {!userEmail && !loading && (
          <div className="mt-8 neon-panel rounded-2xl p-6 text-sm text-gray-300">
            Inicia sesion para ver tu watchlist.
            <div className="mt-3">
              <Link
                href="/auth/login"
                className="text-cyan-200 hover:text-cyan-100"
              >
                Ir a login
              </Link>
            </div>
          </div>
        )}

        {loading && (
          <div className="mt-8 space-y-3">
            {[...Array(4)].map((_, index) => (
              <div key={index} className="h-20 rounded-2xl neon-row opacity-60" />
            ))}
          </div>
        )}

        {error && (
          <div className="mt-6 rounded-2xl bg-red-900/30 border border-red-500/40 p-4 text-xs text-red-200">
            {error}
          </div>
        )}

        {userEmail && !loading && items.length === 0 && (
          <div className="mt-8 neon-panel rounded-2xl p-6 text-sm text-gray-300">
            Todavia no tienes fixtures guardados.
          </div>
        )}

        {userEmail && !loading && items.length > 0 && (
          <div className="mt-8 space-y-4">
            {items.map((item) => (
              <div
                key={item.id}
                className="neon-row rounded-2xl p-4 flex items-center justify-between"
              >
                <div>
                  <p className="text-white font-semibold">
                    {item.fixture.home_team_name}{" "}
                    <span className="text-gray-500">vs</span>{" "}
                    {item.fixture.away_team_name}
                  </p>
                  <p className="text-xs text-gray-400">
                    {new Date(item.fixture.kickoff_time).toLocaleString("es-ES", {
                      weekday: "short",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-400">
                    {item.fixture.status}
                  </span>
                  <button
                    onClick={() => handleRemove(item.id)}
                    className="px-3 py-1 rounded-full border border-red-500/40 text-red-200 text-xs hover:bg-red-500/20"
                  >
                    Quitar
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}