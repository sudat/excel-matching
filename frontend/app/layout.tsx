import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Excel Matching System - Advanced Data Analysis Platform",
  description: "AIによる高度なExcel/CSVファイル分析とマッチングシステム。業務データの効率的な処理と分析を実現します。",
  keywords: "Excel, CSV, データ分析, AI, マッチング, データ処理, 業務効率化",
  robots: "index, follow",
  openGraph: {
    title: "Excel Matching System",
    description: "AIによる高度なデータ分析とマッチングシステム",
    type: "website",
    locale: "ja_JP",
  },
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja" className="scroll-smooth">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased font-sans bg-background text-foreground`}
      >
        <div id="root" className="min-h-screen">
          {children}
        </div>
      </body>
    </html>
  );
}
