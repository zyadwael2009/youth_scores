import type { MetadataRoute } from 'next';

// tla3bny is served at the root of its own subdomain (see next.config.js).
const SITE = 'https://tla3bny.youthscores.org';

// Emit a static /robots.txt at build time (output: 'export').
export const dynamic = 'force-static';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        // Keep the management / auth surfaces out of search results — they are
        // useless to crawlers and gated anyway.
        disallow: ['/admin', '/manage', '/dashboard', '/login', '/register'],
      },
    ],
    host: SITE,
  };
}
