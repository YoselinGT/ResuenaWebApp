/** @type {import('next').NextConfig} */

// La API se consume a través de un rewrite same-origin (/api/* → backend).
// Así la cookie de sesión (HttpOnly + SameSite=Lax) viaja como first-party y
// no requiere CORS ni SameSite=None. En Docker el destino es el servicio `api`;
// en dev local fuera de Docker, localhost:8000.
const API_INTERNAL_URL = process.env.API_INTERNAL_URL || "http://localhost:8000";

const nextConfig = {
  // Salida standalone para imágenes Docker mínimas (ver infra/Dockerfile.app).
  output: "standalone",
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${API_INTERNAL_URL}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
