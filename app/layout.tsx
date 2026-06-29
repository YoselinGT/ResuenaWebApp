import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

// Inter Variable — fuente de marca de Resuena (next/font/local, self-hosted).
const inter = localFont({
  src: [
    {
      path: "./fonts/Inter-Variable.ttf",
      style: "normal",
      weight: "100 900",
    },
    {
      path: "./fonts/Inter-Italic-Variable.ttf",
      style: "italic",
      weight: "100 900",
    },
  ],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Resuena",
  description: "Plataforma de gestión de campañas musicales",
  icons: { icon: "/favicon.png" },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" className={inter.variable}>
      <body>{children}</body>
    </html>
  );
}
