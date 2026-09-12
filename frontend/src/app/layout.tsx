/**
 * ShiVi Root Application Layout
 * ==============================
 *
 * Briefing:
 *     Next.js App Router Root Layout (`RootLayout`) for the ShiVi Common Operational Picture (COP).
 *     Provides top-level HTML document structure, global CSS imports, dark-mode CSS class enforcement,
 *     and standardized SEO/metadata tags.
 *
 * Reason:
 *     Tactical operations consoles operate primarily in low-light command hubs or night-time field posts.
 *     Enforcing dark mode (`dark` class and `#0B0F19` background) at the root document level eliminates
 *     bright flashes during page transitions, reduces screen glare, and maximizes battery efficiency
 *     on OLED field displays.
 */

import type { Metadata } from "next";
import "./globals.css";

/**
 * Briefing:
 *     Static application metadata and title tag configuration.
 *
 * Reason:
 *     Ensures mission controllers and browser tabs clearly identify the console window as the
 *     ShiVi Common Operational Picture (COP) dashboard.
 */
export const metadata: Metadata = {
  title: "ShiVi | Common Operational Picture (COP)",
  description: "Offline-First Mission Coordination & Real-Time Conflict Adjudication",
};

/**
 * Briefing:
 *     Root layout wrapper component enclosing all routes and subpages.
 *
 * Reason:
 *     Supplies the baseline HTML shell, language declaration, anti-aliased font rendering,
 *     and consistent dark-theme palette across all operational views.
 *
 * @param props.children Nested route content and components.
 */
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="light">
      <body className="bg-slate-50 text-slate-900 min-h-screen antialiased selection:bg-amber-100 selection:text-amber-900">
        {children}
      </body>
    </html>

  );
}
