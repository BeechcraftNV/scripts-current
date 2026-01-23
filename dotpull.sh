#!/bin/bash

# Script: dotpull.sh
# Description: Pull latest chezmoi dotfile changes from GitHub and apply

set -euo pipefail

echo "📁 Moving into chezmoi repo..."
chezmoi cd

echo "📥 Pulling from GitHub..."
git pull --rebase

echo "🔄 Applying changes to home directory..."
chezmoi apply

echo "✅ Done."
