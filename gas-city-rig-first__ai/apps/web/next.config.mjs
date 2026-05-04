/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Workspace packages are linked as source — Next must transpile them.
  transpilePackages: ["@gas-city/shared", "@gas-city/poker-core"],
  async rewrites() {
    const target = process.env.SERVER_URL ?? "http://localhost:4000";
    return [
      {
        source: "/api/games",
        destination: `${target}/games`,
      },
      {
        source: "/api/games/:path*",
        destination: `${target}/games/:path*`,
      },
    ];
  },
};

export default nextConfig;
