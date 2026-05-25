import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NextUp — Marketplace di stampa 3D P2P",
  description:
    "Marketplace P2P che collega clienti hobbisti, progettisti 3D e maker. Escrow, protezione IP e logistica integrata.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="it">
      <body>{children}</body>
    </html>
  );
}
