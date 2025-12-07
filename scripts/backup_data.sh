#!/usr/bin/env bash
set -e

SRC_DB="data/crypto_projects.db"
DEST_DIR="backups"
mkdir -p "$DEST_DIR"

if [ -f "$SRC_DB" ]; then
  TS=$(date +"%Y%m%d_%H%M%S")
  cp "$SRC_DB" "$DEST_DIR/crypto_projects_${TS}.db"
  echo "Backup создан: $DEST_DIR/crypto_projects_${TS}.db"
else
  echo "База не найдена по пути $SRC_DB"
fi
