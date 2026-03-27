# 21csim.com — Domain, Hosting & Web Infrastructure Spec

---

## Domain Registration

### Primary Domain

```
21csim.com
```

### Defensive Registrations

Register simultaneously to protect the brand and redirect traffic:

```
21csim.com       → Primary (serves the site)
21csim.org       → 301 redirect to 21csim.com
21csim.dev       → 301 redirect to 21csim.com
21csim.net       → 301 redirect to 21csim.com (if available and cheap)
```

### Registrar

**Cloudflare Registrar** — at-cost pricing (~$10/yr for .com), free DNSSEC, free WHOIS privacy, integrates natively with Cloudflare Pages and DNS.

### DNS

Managed via Cloudflare DNS (automatic when registered through Cloudflare). Benefits: global anycast, automatic DNSSEC, sub-millisecond resolution, DDoS protection on DNS layer.

```
Type    Name              Value                         Proxy
A       21csim.com        → Cloudflare Pages (auto)     Proxied
CNAME   www               → 21csim.com                  Proxied
CNAME   _domainconnect    → (Cloudflare auto)           DNS only
TXT     21csim.com        → verify ownership records    DNS only
```

---

## Hosting

### Platform: Cloudflare Pages

**Why Cloudflare Pages:**
- Free tier covers everything we need (unlimited bandwidth, 500 builds/month)
- Global CDN (300+ edge locations) — site loads fast everywhere
- Deploy from GitHub (push to main → auto-deploy in ~30 seconds)
- Preview deployments on every PR (each PR gets a unique URL)
- Native integration with Cloudflare domain/DNS
- No server to manage, no containers, no scaling concerns
- Free SSL/TLS (automatic, managed certificates)

**Cost: $0/month.** The free tier has no bandwidth limits, no page view limits, and supports custom domains. The only cost is the domain registration (~$10/year).

### Build Configuration

```yaml
# Cloudflare Pages build settings
Framework preset:    None (static output)
Build command:       npm run build
Build output:        dist/
Root directory:      web/
Node version:        20
```

### Deployment Pipeline

```
Developer pushes to GitHub (north-echo/21csim)
  → Cloudflare Pages webhook triggers
    → Build runs (npm run build in web/ directory)
      → Static files deployed to global CDN
        → Live at 21csim.com within ~30 seconds

PR opened → Preview deployment at:
  https://<pr-hash>.21csim.pages.dev
```

---

## Site Architecture

### URL Structure

```
21csim.com/                         Landing page / viewer (the product IS the homepage)
21csim.com/century/{seed}           Individual run permalink (e.g., /century/7714)
21csim.com/explore                  Browse and filter the 200 curated seeds
21csim.com/findings                 Batch analysis dashboard (10K run statistics)
21csim.com/about                    Methodology, probability calibration, sources
21csim.com/about/nodes              Interactive node catalog (browse all 350+ nodes)
21csim.com/about/faq                How it works, what it is, what it isn't
21csim.com/blog                     Blog index
21csim.com/blog/21csim-launch       Launch post
21csim.com/blog/{future-posts}      Future write-ups, analysis, community contributions
```

### Routing

All routes are client-side (SPA with static pre-rendering). Cloudflare Pages handles this with a `_redirects` file:

```
# web/public/_redirects
/century/*    /index.html    200
/explore      /index.html    200
/findings     /index.html    200
/about/*      /index.html    200
/blog/*       /index.html    200
```

Or if using Astro/Next.js static export, each route is pre-rendered as its own HTML file — no redirects needed, better SEO.

---

## Tech Stack

### Static Site Framework

**Astro** (preferred) or Next.js static export.

Astro is the better fit because:
- Static-first by default (no hydration unless explicitly opted in)
- React components work inside Astro pages (for the interactive viewer)
- Markdown/MDX for blog posts with zero config
- Built-in image optimization
- Smaller bundle size than Next.js for a mostly-static site
- Partial hydration means the viewer is interactive but the blog/about pages are pure HTML

```
web/
├── astro.config.mjs
├── src/
│   ├── layouts/
│   │   ├── BaseLayout.astro          # Shared HTML head, nav, footer
│   │   └── BlogLayout.astro          # Blog post template
│   ├── pages/
│   │   ├── index.astro               # Landing → mounts <CenturyViewer />
│   │   ├── century/[seed].astro      # Dynamic route for run permalinks
│   │   ├── explore.astro             # Seed browser
│   │   ├── findings.astro            # Batch dashboard
│   │   ├── about/
│   │   │   ├── index.astro           # Methodology
│   │   │   ├── nodes.astro           # Node catalog
│   │   │   └── faq.astro
│   │   └── blog/
│   │       ├── index.astro           # Blog listing
│   │       └── 21csim-launch.mdx     # Launch post
│   ├── components/                    # React components (hydrated)
│   │   ├── CenturyViewer.tsx
│   │   ├── Timeline.tsx
│   │   ├── WorldStatePanel.tsx
│   │   ├── RegionMap.tsx
│   │   ├── ComparisonBars.tsx
│   │   ├── ButterflyDiagram.tsx
│   │   ├── EraTransition.tsx
│   │   ├── EventCard.tsx
│   │   ├── RunSelector.tsx
│   │   ├── SpeedControl.tsx
│   │   ├── SpecialMoments.tsx
│   │   ├── FinalSummary.tsx
│   │   ├── BatchDashboard.tsx
│   │   └── NodeCatalog.tsx
│   ├── audio/
│   │   └── SoundEngine.ts            # Web Audio API synthesis
│   ├── data/
│   │   └── types.ts                   # TypeScript types
│   └── styles/
│       └── global.css                 # Tailwind + custom properties
├── public/
│   ├── runs/                          # Pre-generated JSON (200 curated seeds)
│   │   ├── index.json                 # Catalog with metadata for all seeds
│   │   ├── 42.json
│   │   ├── 7714.json
│   │   └── ...
│   ├── batch/
│   │   └── 10k-analysis.json          # Pre-computed batch statistics
│   ├── og/                            # Pre-generated social cards
│   │   ├── default.png
│   │   ├── 42.png
│   │   ├── 7714.png
│   │   └── ...
│   ├── favicon.svg
│   └── robots.txt
├── package.json
└── tailwind.config.js
```

### Styling

**Tailwind CSS** with custom properties for the dark terminal aesthetic:

```css
/* src/styles/global.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --bg-primary: #06060a;
  --bg-secondary: #08080c;
  --bg-tertiary: #0c0c12;
  --border: #111118;
  --text-primary: #d0d0d8;
  --text-secondary: #a0a0a8;
  --text-dim: #555;
  --text-ghost: #222;
  --accent-gold: #c49a28;
  --accent-green: #38a868;
  --accent-red: #b83838;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', 'Menlo', monospace;
}
```

### Typography

**JetBrains Mono** as the primary (and only) font. Self-hosted from `/public/fonts/` to avoid Google Fonts dependency and improve load time.

```html
<!-- Preload the font for faster rendering -->
<link rel="preload" href="/fonts/JetBrainsMono-Regular.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/JetBrainsMono-Bold.woff2" as="font" type="font/woff2" crossorigin>
```

---

## Performance Budget

The site should feel instant. Target metrics:

| Metric | Target |
|--------|--------|
| First Contentful Paint | < 0.8s |
| Largest Contentful Paint | < 1.5s |
| Time to Interactive | < 2.0s |
| Total page weight (landing) | < 500KB |
| Total page weight (viewer + 1 run JSON) | < 800KB |
| Lighthouse Performance score | > 95 |

### How to hit these targets:

- **Self-hosted font** (no external request to Google Fonts)
- **Astro partial hydration** — only the viewer component is interactive; everything else is static HTML
- **JSON runs loaded on demand** — not bundled; fetched when a seed is selected
- **No heavy frameworks** — no chart libraries except for the findings page; viewer uses inline SVG and CSS
- **Cloudflare CDN** — assets cached at 300+ edge locations
- **Image optimization** — social cards pre-generated as optimized PNGs; no runtime image processing
- **Code splitting** — viewer component loaded only on pages that need it

---

## Social Sharing & SEO

### Open Graph / Twitter Cards

Every run permalink generates a unique social card. Pre-generate these during `export-library` as static PNGs stored in `/public/og/`.

```html
<!-- Default (landing page) -->
<meta property="og:title" content="21csim — The 21st Century Simulator">
<meta property="og:description" content="What if history had gone differently? Watch 10,000 alternate centuries unfold.">
<meta property="og:image" content="https://21csim.com/og/default.png">
<meta property="og:url" content="https://21csim.com">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="21csim — The 21st Century Simulator">
<meta name="twitter:description" content="What if history had gone differently?">
<meta name="twitter:image" content="https://21csim.com/og/default.png">

<!-- Per-seed (e.g., /century/7714) -->
<meta property="og:title" content="Seed 7714 — The Near-Miss Century">
<meta property="og:description" content="PROGRESS (+0.45) · Gore wins, no Iraq, climate barely averted. 147 divergences from our timeline.">
<meta property="og:image" content="https://21csim.com/og/7714.png">
<meta property="og:url" content="https://21csim.com/century/7714">
```

### Social Card Design (Pre-Generated PNG)

```
┌──────────────────────────────────────────────────┐
│                                                    │
│  21csim.com                                        │
│                                                    │
│  THE 21st CENTURY · Seed 7714                      │
│                                                    │
│  "The Near-Miss Century:                           │
│   Climate Crisis Barely Averted"                   │
│                                                    │
│  PROGRESS · +0.45 · 65th percentile                │
│  147 divergences from our timeline                 │
│                                                    │
│  Watch it unfold →                                 │
│                                                    │
└──────────────────────────────────────────────────┘
```

Dark background (#06060a), gold accent text (#c49a28), JetBrains Mono font. Dimensions: 1200x630px (standard OG image size).

Generate these with a Node.js script using `@vercel/og` or `satori` + `sharp`:

```bash
# During export-library
21csim export-library --count 200 --narrate --social-cards --output web/public/
```

### SEO

```html
<!-- Structured data for search engines -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "21csim",
  "description": "Monte Carlo counterfactual simulator for the 21st century",
  "url": "https://21csim.com",
  "applicationCategory": "Simulation",
  "operatingSystem": "Web Browser",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  }
}
</script>
```

```
# public/robots.txt
User-agent: *
Allow: /
Sitemap: https://21csim.com/sitemap.xml
```

Astro generates `sitemap.xml` automatically with the `@astrojs/sitemap` integration.

---

## Security

### Headers (Cloudflare Pages `_headers` file)

```
# web/public/_headers

/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self' https://api.anthropic.com; media-src 'self'
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload

/fonts/*
  Cache-Control: public, max-age=31536000, immutable

/runs/*
  Cache-Control: public, max-age=86400

/og/*
  Cache-Control: public, max-age=604800
```

**Note:** `connect-src` includes `api.anthropic.com` only for users who opt in to real-time Claude narration via their own API key. The default experience makes zero external API calls.

### HTTPS

Automatic via Cloudflare. Full (strict) SSL mode. HSTS preload enabled.

### Privacy

- **No cookies** (unless user opts into API key storage, which uses localStorage only)
- **No analytics** by default. If analytics are added later, use Cloudflare Web Analytics (privacy-preserving, no cookies, included free)
- **No tracking pixels, no third-party scripts**
- **No user accounts** — the site is fully static and anonymous
- **WHOIS privacy** included with Cloudflare Registrar

---

## Monitoring

### Uptime & Performance

**Cloudflare Web Analytics** (free, privacy-preserving):
- Page views, unique visitors, performance metrics
- Core Web Vitals tracking
- No JavaScript tag required (DNS-level analytics)

### Error Monitoring

For the interactive viewer components, add minimal client-side error reporting:

```typescript
// Catch unhandled errors in the viewer
window.addEventListener('error', (event) => {
  // Log to Cloudflare Analytics custom event (if enabled)
  // Or simply console.error — for a static site, most errors are non-critical
  console.error('21csim viewer error:', event.message);
});
```

No Sentry, no DataDog, no paid error monitoring. The site is static — if it works in testing, it works in production.

---

## Cost Summary

| Item | Provider | Cost |
|------|----------|------|
| Domain: 21csim.com | Cloudflare Registrar | ~$10/year |
| Domain: 21csim.org | Cloudflare Registrar | ~$10/year |
| Domain: 21csim.dev | Cloudflare Registrar | ~$12/year |
| Hosting | Cloudflare Pages (free tier) | $0/month |
| CDN | Cloudflare (included) | $0/month |
| SSL/TLS | Cloudflare (included) | $0/month |
| DNS | Cloudflare (included) | $0/month |
| Analytics | Cloudflare Web Analytics | $0/month |
| DDoS Protection | Cloudflare (included) | $0/month |
| **Total Year 1** | | **~$32/year** |
| **Total Ongoing** | | **~$32/year** |

The entire web presence runs for about $3/month. No servers, no containers, no scaling concerns, no ops burden.

---

## Deployment Checklist

### Before Launch

```
[ ] Register 21csim.com via Cloudflare Registrar
[ ] Register 21csim.org, 21csim.dev (redirect to .com)
[ ] Enable DNSSEC on all domains
[ ] Create Cloudflare Pages project linked to north-echo/21csim
[ ] Configure build settings (web/ directory, npm run build)
[ ] Configure custom domain (21csim.com → Pages project)
[ ] Configure www redirect (www.21csim.com → 21csim.com)
[ ] Upload pre-generated run JSONs to web/public/runs/
[ ] Upload pre-generated social cards to web/public/og/
[ ] Upload batch analysis data to web/public/batch/
[ ] Self-host JetBrains Mono font files
[ ] Set security headers (_headers file)
[ ] Set redirect rules (_redirects file)
[ ] Generate and verify sitemap.xml
[ ] Test all routes (/, /century/7714, /explore, /findings, /about, /blog)
[ ] Test social cards (use https://cards-dev.twitter.com/validator)
[ ] Test Open Graph (use https://developers.facebook.com/tools/debug/)
[ ] Run Lighthouse audit (target >95 performance)
[ ] Test on mobile (responsive layout)
[ ] Test sound engine (Web Audio API) on Chrome, Firefox, Safari
[ ] Enable Cloudflare Web Analytics
[ ] Verify HSTS preload submission
[ ] Push to main → verify auto-deployment works
```

### Launch Day

```
[ ] Merge final PR to main
[ ] Verify deployment at 21csim.com
[ ] Verify all permalinks work
[ ] Submit to Hacker News
[ ] Post on Twitter/Bluesky with a curated seed link
[ ] Submit to relevant subreddits (r/dataisbeautiful, r/alternatehistory, r/simulation)
[ ] Share on LinkedIn with professional framing
[ ] Monitor Cloudflare Analytics for first 24 hours
```

### Post-Launch

```
[ ] Monitor for broken links or rendering issues
[ ] Respond to HN/Reddit comments
[ ] Track which seeds get shared most (via Cloudflare Analytics path data)
[ ] Write follow-up blog post if reception warrants
[ ] Open GitHub Issues for community node contributions
```

---

## Future Infrastructure (If Traffic Warrants)

If the site goes viral and traffic exceeds Cloudflare Pages free tier limits (currently very generous — this is unlikely):

**Tier 1 (free → $20/month):** Cloudflare Pages Pro. Higher build limits, more concurrent builds. Same architecture.

**Tier 2 (if we need server-side features):** Add Cloudflare Workers for:
- Dynamic social card generation (instead of pre-generated PNGs)
- Real-time seed simulation in the browser via WASM
- API endpoint for the scenario builder feature

**Tier 3 (if we need a database):** Cloudflare D1 (serverless SQLite) for:
- User-submitted seeds and narrations
- Community node contributions
- Leaderboard of most-shared seeds

All of this stays within Cloudflare's ecosystem, which means zero migration pain. But for launch, the static site is more than sufficient.
