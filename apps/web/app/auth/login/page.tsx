"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { supabase } from "@/lib/supabase";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    const { error: signInError } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (signInError) {
      setError(signInError.message);
      setLoading(false);
      return;
    }

    router.push("/");
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md neon-panel rounded-2xl p-6">
        <h1 className="text-2xl font-display text-white">Iniciar sesion</h1>
        <p className="mt-2 text-sm text-gray-400">
          Accede para guardar favoritos y recibir alertas.
        </p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="text-xs uppercase tracking-[0.2em] text-cyan-300">
              Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="mt-2 w-full rounded-xl bg-black/40 border border-cyan-500/30 px-4 py-2 text-sm text-white focus:outline-none focus:border-cyan-400"
            />
          </div>
          <div>
            <label className="text-xs uppercase tracking-[0.2em] text-cyan-300">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-2 w-full rounded-xl bg-black/40 border border-cyan-500/30 px-4 py-2 text-sm text-white focus:outline-none focus:border-cyan-400"
            />
          </div>

          {error && (
            <div className="rounded-xl bg-red-900/30 border border-red-500/40 px-3 py-2 text-xs text-red-200">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-cyan-500/20 text-cyan-100 border border-cyan-400/40 py-2 text-sm hover:bg-cyan-500/30 transition-colors disabled:opacity-60"
          >
            {loading ? "Ingresando..." : "Ingresar"}
          </button>
        </form>

        <p className="mt-4 text-xs text-gray-400">
          No tienes cuenta?{" "}
          <Link href="/auth/signup" className="text-cyan-200 hover:text-cyan-100">
            Crear cuenta
          </Link>
        </p>
      </div>
    </div>
  );
}
