# Annika Palermo

**Sample site:** a fictional couture wedding dress designer portfolio. The designer, gowns, posts and quote are fictional.

Website system `annika` on the palermo-sites website platform, built with [Astro](https://astro.build) (static output).
Owner: Jeffrey Palermo. Domain: annikapalermo.com (connected 2026-10-18).

- Live (prod, GitHub Pages): https://annikapalermo.com (www redirects to it; the old github.io address redirects too)
- UAT (GitHub Pages, not indexed): https://uat.annikapalermo.com/, served by
  [palermo-sites/annika-site-uat](https://github.com/palermo-sites/annika-site-uat) (branch `gh-pages`, written only by
  workflow `uat`). Every push to a pull request and every push to `main` replaces it; the URL is commented on the pull request.

## How changes get published

Branch, open a pull request, review it in UAT, merge to publish. Details for people and AI agents: [AGENTS.md](AGENTS.md).
UAT builds with base `/` and `CNAME` `uat.annikapalermo.com`, a `noindex` meta tag, a "UAT, not live" banner and no sitemap (GitHub Pages
cannot send headers). There is **one** UAT site: the newest pull request push or
`main` push wins, so with two open pull requests UAT shows whichever pushed last (push again, or run workflow `uat` by
hand, to put yours back). Credential: secret `UAT_DEPLOY_KEY`, a deploy key with write access to `annika-site-uat` only.
- `src/content/designs/` design notes (blog posts) and `src/content/portfolio/` finished gowns: Astro content collections
  (schemas in `src/content.config.ts`). Add a Markdown file to add a post or a piece.
- `src/pages/` Home, Designs (index and posts), Portfolio (index and pieces), About, Contact (static placeholder form;
  it sends nothing). `src/layouts/Base.astro` holds SEO and Open Graph meta; `@astrojs/sitemap` writes the sitemap.
- Fonts are self-hosted through Fontsource (Cormorant Garamond, Inter; SIL Open Font License).

## Image credits

All illustrations in `public/images/` are original SVG artwork generated for this site by `scripts/make-art.mjs`
(`og.png` is rendered from `og.svg`). No stock or third-party imagery is used.
- `scripts/build.sh` installs and builds into `_site/` (Node 22+). `BASE_PATH` sets the base path for a build served under
  a path; prod and UAT are both served at `/`.
- `ci.yml`: build, HTML check, link check on every push and pull request. `deploy.yml`: GitHub Pages (`prod`) after CI passes on `main`.

```bash
npm install
npm run dev          # http://localhost:4321
bash scripts/build.sh
```

## annikapalermo.com

DNS (2026-10-18): apex `@` four `A` records `185.199.108.153` to `185.199.111.153`; `www` and `uat` `CNAME`
`palermo-sites.github.io`. Prod: `public/CNAME` `annikapalermo.com` and the Pages custom domain of this repository (www
redirects to the apex). UAT: workflow `uat` writes `CNAME` `uat.annikapalermo.com` into the build it pushes to
`annika-site-uat`. HTTPS is enforced on both.

## Delivery scorecard

`.github/workflows/scorecard.yml` records this site's delivery facts every day at 06:17 UTC (or by hand: Actions → Daily
scorecard → Run workflow, with an optional backfill range `days` and `force`). The site is the system level of the platform,
so its scorecard lives here (kit decisions 0005, 0006). GitHub only, no Azure or Octopus Deploy: items and stage moves come from
cmis over this repository's issues, pull requests and commits; deployments are GitHub Actions runs in environment order UAT, then prod (`deploy.yml` on `main` = prod,
`uat.yml` = UAT; older `staging.yml` pull request runs count as UAT too), configured in `.github/scorecard/config.json`.

A day is a calendar day in America/New_York. Output goes to the `scorecard-data` branch, never to `main`:

- `days/YYYY-MM-DD.json`: one per finished day, written once: additive counts (started, delivered, forward moves, rework,
  stopped, end-of-day work in process), delivery durations (list and sum), item and move events with timestamps, deployments per
  environment with each run's outcome
- `daily.json`: compact counts of every day plus today so far, each with `hours` (per America/New_York hour; quiet hours omitted, work in process at hour end); the dashboard groups it in the browser
- `latest.json`: today so far (provisional), the last finished day, and the named views (rolling 7/30/90 days, Rolling 12 weeks/months)
- `index.html`: the report: rolling views, then by ISO week, month, quarter, day, hour (48 hours) and an hour-of-day profile (0–23)

Grouping rules: counts are summed; MTTD = total delivery time / items delivered (never an average of averages); work in process is
the last day's value; failed share = failed / deployments. Each run shows the report on its Summary page and uploads the styled
HTML as the artifact `scorecard-report`. A rerun with unchanged numbers commits nothing.
Secret: `SCORECARD_SOURCE_TOKEN` (read access to the scorecard source, to build cmis).
