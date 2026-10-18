# Annika Palermo

**Sample site:** a fictional couture wedding dress designer portfolio. The designer, gowns, posts and quote are fictional.

Website system `annika` on the palermo-sites website platform, built with [Astro](https://astro.build) (static output).
Owner: Jeffrey Palermo. Final domain: annikapalermo.com (not yet connected; see below).

- Live (prod, GitHub Pages): https://palermo-sites.github.io/annika-site/
- Staging (stable, not indexed): https://thankful-island-0db965a0f.3.azurestaticapps.net (branch `staging`)
- Pull request previews: each pull request gets its own URL, posted as a comment on it (Azure Static Web Apps,
  `rg-palermo-sites-sites/annika-site-staging`, Free tier: up to 3 previews at once).

## How changes get published

Branch, open a pull request, review its preview URL, merge to publish. Details for people and AI agents: [AGENTS.md](AGENTS.md).
Staging and previews build with base `/`, a `noindex` meta tag, an `X-Robots-Tag: noindex` header and a robots.txt
that disallows everything (`staging/`). To refresh the stable staging URL, push to the `staging` branch
(`git push origin main:staging` mirrors main).
- `src/content/designs/` design notes (blog posts) and `src/content/portfolio/` finished gowns: Astro content collections
  (schemas in `src/content.config.ts`). Add a Markdown file to add a post or a piece.
- `src/pages/` Home, Designs (index and posts), Portfolio (index and pieces), About, Contact (static placeholder form;
  it sends nothing). `src/layouts/Base.astro` holds SEO and Open Graph meta; `@astrojs/sitemap` writes the sitemap.
- Fonts are self-hosted through Fontsource (Cormorant Garamond, Inter; SIL Open Font License).

## Image credits

All illustrations in `public/images/` are original SVG artwork generated for this site by `scripts/make-art.mjs`
(`og.png` is rendered from `og.svg`). No stock or third-party imagery is used.
- `scripts/build.sh` installs and builds into `_site/` (Node 22+). `BASE_PATH` sets the base path (the deploy workflow
  passes `/annika-site` while served from github.io).
- `ci.yml`: build, HTML check, link check on every push and pull request. `deploy.yml`: GitHub Pages (`prod`) after CI passes on `main`.

```bash
npm install
npm run dev          # http://localhost:4321
bash scripts/build.sh
```

## Connecting annikapalermo.com

The domain is not set yet: setting it before DNS exists would redirect the github.io address to a domain that does not
resolve. When ready:

1. At the DNS provider for annikapalermo.com:
   - apex `@`: four `A` records `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
     (optionally `AAAA` `2606:50c0:8000::153` ... `8003::153`);
   - `www`: `CNAME` to `palermo-sites.github.io`.
2. (Recommended) verify the domain for the `palermo-sites` org: GitHub org Settings, Pages, Add a domain (TXT record).
3. Add `public/CNAME` containing `annikapalermo.com`, and in `deploy.yml` stop passing `BASE_PATH` (base becomes `/`).
4. Repository Settings, Pages: custom domain `annikapalermo.com`, then tick "Enforce HTTPS" once the certificate is issued.
