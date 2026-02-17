# Docs website via GitHub (custom domain)

This document describes a simple approach to host user documentation from GitHub on a website at `http://docs.corpusanalytica.com/`.

## Recommended stack

- **Docs generator**: MkDocs
- **Theme**: Material for MkDocs
- **Hosting**: GitHub Pages
- **Custom domain**: `docs.corpusanalytica.com`

## Why this approach

- Documentation source-of-truth stays in **GitHub** (markdown + config in the repo).
- MkDocs Material provides a high-quality docs UX (navigation, search, code formatting).
- GitHub Pages provides reliable hosting with minimal infrastructure.

## Repository layout

At minimum:

- `mkdocs.yml` (repo root)
- `docs/` (markdown pages)

Optional later:

- `overrides/` (theme overrides)

## Hosting model (GitHub Pages)

Recommended hosting mode:

- Build and deploy the docs site from the **`main` branch** to a **`gh-pages` branch**.
- GitHub Pages serves the site from the **`gh-pages` branch**.

This keeps authoring simple (everything lives in `main`) while hosting remains static and fast.

## Custom domain setup (`docs.corpusanalytica.com`)

### DNS

Create a DNS record for the subdomain:

- **CNAME**
  - Name/Host: `docs`
  - Target/Value: `<your-org>.github.io`

(Replace `<your-org>` with your GitHub organization or username.)

### GitHub Pages settings

In the repo:

- Settings -> Pages
- Source: `Deploy from a branch`
- Branch: `gh-pages` (root)
- Custom domain: `docs.corpusanalytica.com`
- Enable: **Enforce HTTPS** (after certificate provisioning completes)

GitHub will automatically provision TLS certificates after DNS is correct (may take minutes to hours).

## Suggested workflow

Publish docs from `main` whenever you merge changes.

Common patterns:

- Deploy on every push to `main`.
- Or deploy only when you merge PRs labeled as docs (process choice).

## Notes / alternatives

### Mintlify

Mintlify can also host GitHub-backed docs with a custom domain and offers a very polished look.

Tradeoffs compared to MkDocs + `mike`:

- Pros: very polished UI quickly, less DIY theming
- Cons: more platform coupling; versioning workflow may be less flexible than `mike`

### Docusaurus

Good if you want a combined marketing site + docs + blog, and you’re comfortable with a Node/React toolchain.

## Optional later: versioned docs (via `mike`)

If you later need to support multiple released versions of your product (and keep matching docs per version), you can add `mike`.

High-level model:

- `mike` publishes each version of the built docs to GitHub Pages under a versioned path.

Recommended conventions:

- Release versions: `1.0`, `1.1`, `2.0` (whatever matches your release strategy)
- Aliases:
  - `latest` -> newest released docs
  - optional `stable` -> the version you consider production-stable

Typical resulting URLs:

- `http://docs.corpusanalytica.com/latest/`
- `http://docs.corpusanalytica.com/1.2/`
- `http://docs.corpusanalytica.com/2.0/`

## Current decision

The docs site reflects the current state of the `main` branch.
