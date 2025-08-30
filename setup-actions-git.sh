#!/usr/bin/env bash
set -euo pipefail

echo "==> Setting up GitHub Actions workflows..."

# Ensure we're at repo root
if [ ! -d ".git" ]; then
  echo "❌ Error: This doesn’t look like the root of a Git repository."
  exit 1
fi

mkdir -p .github/workflows

# CI + GitHub Pages workflow
cat > .github/workflows/ci-pages.yml <<'YAML'
name: CI & Deploy (Pages)

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm test --if-present
      - run: npm run build --if-present
      - uses: actions/upload-pages-artifact@v3
        with:
          path: dist
  deploy:
    needs: build
    runs-on: ubuntu-latest
    permissions:
      pages: write
      id-token: write
    steps:
      - uses: actions/deploy-pages@v4
YAML

# Docker Publish workflow
cat > .github/workflows/docker-publish.yml <<'YAML'
name: Docker Build & Publish (GHCR)

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

permissions:
  contents: read
  packages: write

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=ref,event=tag
            type=sha
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
YAML

# Stage for commit
git add .github/workflows
echo "✅ Workflows created and staged."

# Ask user if they want to commit now
read -rp "Do you want to commit these changes now? (y/n) " answer
if [[ "$answer" =~ ^[Yy]$ ]]; then
  read -rp "Enter commit message: " msg
  git commit -m "$msg"
  echo "✅ Committed with message: $msg"
else
  echo "ℹ️  Skipped commit. Files are staged — commit later with:"
  echo "   git commit -m 'your message'"
fi

