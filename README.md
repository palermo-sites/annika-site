# Annika Palermo

Website system `annika` on the palermo-sites website platform. Owner: Jeffrey Palermo. Domain: annikapalermo.com.

- `site/` holds the website. Replace it with any generator you like; `scripts/build.sh` must leave the built site in `_site/`.
- `ci.yml` builds and checks every pull request and push (`build`, `links`, `html`) and uploads a preview artifact.
- `deploy.yml` deploys `_site/` to GitHub Pages (environment `prod`) after CI passes on `main`.

```bash
bash scripts/build.sh && python3 -m http.server -d _site 8000
```
