import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SmartFactory Móveis AI",
  description: "ERP para marcenarias e fábricas de móveis planejados",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
