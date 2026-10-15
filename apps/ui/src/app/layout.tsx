import React, { Suspense } from "react";
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Navbar } from "@/components/navbar";
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
  title: "Varistha | AI Employee Control Plane",
  description: "Self-hostable control plane to build, run, monitor and govern AI employees for startups.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-background text-foreground font-sans">
        <Suspense fallback={<div className="h-14 border-b border-border/80" />}>
          <Navbar />
        </Suspense>
        <main className="flex-1 py-8 px-4 sm:px-6">
          <div className="container mx-auto max-w-7xl">
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}
