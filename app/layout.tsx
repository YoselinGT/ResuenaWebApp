import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Resuena",
  description: "Plataforma de gestión de campañas musicales",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
