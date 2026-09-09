const withPWA = require('next-pwa')({
  dest: 'public',
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === 'development',
  runtimeCaching: [
    // Never cache the API. Most /api/tla3bny/ management calls carry a bearer
    // token (academy/team/admin sessions); a cached response would otherwise
    // persist in script-readable Cache Storage past logout, and stale league
    // data has little offline value for a management app. Listed first so it
    // wins over the default "/api/" NetworkFirst rule. Static pages/assets still
    // get offline caching from the defaults below.
    {
      urlPattern: ({ url }) => url.pathname.startsWith('/api/'),
      handler: 'NetworkOnly',
    },
    ...require('next-pwa/cache'),
  ],
});

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

module.exports = withPWA(nextConfig);
