# AGENTS.md

Rules for AI agent sessions (and people) changing the website system `annika` (annikapalermo.com, Astro).

## The workflow: branch, pull request, preview, merge

1. **Never push to `main`.** Every push to `main` publishes the live site. `main` is protected: changes arrive only by
   pull request, and CI must pass.
2. **Create a branch** from the latest `main`, named for the change, for example `add-gown-isla` or `fix-about-typo`.
3. **Make the change and check it locally:** `npm ci && npm run build` (Node 22+) must succeed. `npm run dev` shows it
   at http://localhost:4321.
4. **Push the branch and open a pull request** into `main`. Describe what changed in plain words.
5. **Wait for the checks and the preview.** Workflow `ci` builds the site and checks HTML and links. Workflow `staging`
   deploys the pull request to its own preview URL (`https://thankful-island-0db965a0f-<n>.eastus2.3.azurestaticapps.net`)
   and posts that URL as a comment on the pull request. Each new push to the branch updates the same preview.
6. **Review the preview** (give the URL to Annika). Fix anything on the same branch; the preview updates.
7. **Merge the pull request** when Annika approves. The merge publishes to the live site on GitHub Pages in about two
   minutes (`ci`, then `deploy`). The preview is deleted when the pull request closes.

If a check fails, read its log, fix it on the branch, and push again. Do not bypass a failing check.

## Where things are

- Gowns: one Markdown file per gown in `src/content/portfolio/`. Design notes (blog posts): `src/content/designs/`.
  Front matter fields are defined in `src/content.config.ts`; copy an existing file as a starting point.
- Pages: `src/pages/`. Shared layout, SEO and Open Graph: `src/layouts/Base.astro`. Styles: `src/styles/global.css`.
- Images: `public/images/`; reference them by file name in front matter. Only use images you have the right to use, and
  record credits in README.md.
- Links inside pages must use `url('/path/')` from `src/lib.ts` so they work under any base path.

## Rules

- No secrets in files, commits or pull requests.
- Do not edit `.github/workflows/` or `staging/` without asking Jeffrey: they are the platform's delivery pipeline.
- The contact form must stay a placeholder (sends nothing) until a real form service is chosen.
- Keep the site accessible: alt text for every meaningful image, headings in order, visible focus.
