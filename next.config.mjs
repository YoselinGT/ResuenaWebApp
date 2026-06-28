/** @type {import('next').NextConfig} */
const nextConfig = {
  // Salida standalone para imágenes Docker mínimas (ver infra/Dockerfile.app).
  output: "standalone",
  reactStrictMode: true,
};

export default nextConfig;
