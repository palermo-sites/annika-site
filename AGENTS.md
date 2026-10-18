# AGENTS.md

Rules for agent sessions in the website system `annika`.

- `main` is always deployable: every push to it deploys to `prod`. Work on a branch and open a pull request.
- CI (`build`, `links`, `html`) must pass before merging. Run `bash scripts/build.sh` locally first.
- The build output goes to `_site/` and is never committed.
- No secret in a file, a command-line argument or a commit; use the repository's environment secrets.
- The owner, Jeffrey Palermo, merges pull requests. Template changes from the platform arrive as pull requests.
