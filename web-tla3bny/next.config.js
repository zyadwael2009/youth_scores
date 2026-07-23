/** @type {import('next').NextConfig} */
// Standalone tla3bny app, served at the root of tla3bny.youthscores.org.
// Static export (like the main youthscores web) so it can be served by Flask or
// any static host. No basePath: its routes ARE the subdomain root (/, /standings,
// /admin, ...), which is the whole point of the separate build.
const nextConfig = {
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
    remotePatterns: [{ protocol: 'https', hostname: '**' }],
  },
};

module.exports = nextConfig;
