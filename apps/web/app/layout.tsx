import type { Metadata } from "next";
import { Orbitron, Rajdhani } from "next/font/google";
import "./globals.css";

const orbitron = Orbitron({
  subsets: ["latin"],
  weight: ["400", "600", "700"],
  variable: "--font-orbitron",
});

const rajdhani = Rajdhani({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-rajdhani",
});

export const metadata: Metadata = {
  title: "Marc Loyera Picks - Smart Betting Only",
  description:
    "Neon-style football picks ranking with model confidence and market insights. Solo fines educativos 18+.",
  keywords: [
    "football",
    "betting",
    "picks",
    "sports analytics",
    "machine learning",
    "pronosticos futbol",
  ],
  authors: [{ name: "Marc Loyera Picks" }],
  manifest: "/manifest.json",
  themeColor: "#06b6d4",
  viewport: {
    width: "device-width",
    initialScale: 1,
    maximumScale: 1,
  },
  openGraph: {
    title: "Marc Loyera Picks",
    description: "Smart Betting Only — Neon Picks Board",
    type: "website",
    locale: "es_MX",
  },
  twitter: {
    card: "summary_large_image",
    title: "Marc Loyera Picks",
    description: "Smart Betting Only — Neon Picks Board",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body
        className={`${orbitron.variable} ${rajdhani.variable} bg-[#05040b] text-white antialiased font-body`}
      >
        <div className="relative min-h-screen">{children}</div>
      </body>
    </html>
  );
}
