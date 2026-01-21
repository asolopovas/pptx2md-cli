#!/usr/bin/env bash
set -euo pipefail

WITH_DEPS=false
FORCE=false

for arg in "$@"; do
  case "$arg" in
    --dependencies)
      WITH_DEPS=true
      ;;
    --force)
      FORCE=true
      ;;
    *)
      printf "Unknown option: %s\n" "$arg"
      exit 1
      ;;
  esac
done

if ! command -v uv >/dev/null 2>&1; then
  printf "Installing uv...\n"
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

if "$WITH_DEPS"; then
  if command -v apt-get >/dev/null 2>&1; then
    printf "Installing ImageMagick and WMF/EMF support...\n"
    sudo apt-get update
    sudo apt-get install -y imagemagick libwmf-bin emf2svg libmagickcore-6.q16-7-extra
  else
    printf "Install ImageMagick, libwmf-bin, emf2svg manually for your OS.\n"
    exit 1
  fi
fi

INSTALL_ARGS=("tool" "install" "-e" ".")
if "$FORCE"; then
  INSTALL_ARGS+=("--force")
fi

uv "${INSTALL_ARGS[@]}"
