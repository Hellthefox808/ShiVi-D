import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ShiVi | Common Operational Picture (COP)",
  description: "Offline-First Mission Coordination & Real-Time Conflict Adjudication",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0B0F19] text-slate-100 min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}
