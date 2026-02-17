# Tasks: docs website (GitHub + custom domain)

Goal: Host documentation from this GitHub repo on `http://docs.corpusanalytica.com/` using MkDocs Material.

## Checklist

## 1) Add docs structure to the repo

- [x] Create `docs/` folder
- [x] Add `docs/index.md`
- [x] Add at least one additional page (e.g. `docs/getting-started.md`)
- [x] Create `mkdocs.yml` at repo root
- [x] Add navigation entries for the pages in `mkdocs.yml`

## 2) Add dependencies and verify locally

- [ ] Add/install Python dependencies:
  - [x] `mkdocs`
  - [x] `mkdocs-material`
- [ ] Run locally: `mkdocs serve`
- [ ] Verify pages render and navigation works

## 3) Automate deployment from `main` to `gh-pages`

- [x] Create a GitHub Actions workflow that runs on push to `main`
- [ ] Workflow steps:
  - [x] Checkout repository
  - [x] Install Python + dependencies
  - [x] Build MkDocs site
  - [x] Publish output to `gh-pages` branch

## 4) Configure GitHub Pages

- [ ] Repo -> Settings -> Pages
- [ ] Source: `Deploy from a branch`
- [ ] Branch: `gh-pages` (root)

## 5) Configure custom domain + HTTPS

- [ ] DNS provider:
  - [ ] Add CNAME record: `docs` -> `<org>.github.io`
- [ ] Repo -> Settings -> Pages:
  - [ ] Set custom domain to `docs.corpusanalytica.com`
  - [ ] Enable **Enforce HTTPS** (after cert is issued)

## 6) Smoke test

- [ ] Confirm `http://docs.corpusanalytica.com/` loads
- [ ] Confirm a change merged to `main` redeploys the site

## Optional later

- [ ] Add “Edit this page” links to GitHub
- [ ] Add a docs contribution guide
- [ ] Add versioned docs using `mike` if you later need per-release documentation
