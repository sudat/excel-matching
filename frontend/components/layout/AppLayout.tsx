"use client";

import React from "react";
import Header from "./Header";

interface AppLayoutProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  showNavigation?: boolean;
  className?: string;
}

export default function AppLayout({
  children,
  title,
  subtitle,
  showNavigation = true,
  className = "min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50",
}: AppLayoutProps) {
  return (
    <div className={className}>
      <Header
        title={title}
        subtitle={subtitle}
        showNavigation={showNavigation}
      />
      <main className="w-full max-w-7xl mx-auto px-4 py-8">{children}</main>
    </div>
  );
}
