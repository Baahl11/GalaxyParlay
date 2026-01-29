import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'ParlayGalaxy - Smart Football Betting Intelligence',
  description: 'Data-driven football predictions with transparent quality scoring and interactive Galaxy visualization.',
  keywords: ['football', 'betting', 'predictions', 'sports analytics', 'machine learning'],
  authors: [{ name: 'ParlayGalaxy Team' }],
  openGraph: {
    title: 'ParlayGalaxy',
    description: 'Smart Football Betting Intelligence Platform',
    type: 'website',
    locale: 'en_US',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'ParlayGalaxy',
    description: 'Smart Football Betting Intelligence Platform',
  },
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
  },
  themeColor: '#1B2735',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={`${inter.className} bg-gray-950 text-white antialiased`}>
        <div className="relative min-h-screen">
          {children}
        </div>
      </body>
    </html>
  );
}
