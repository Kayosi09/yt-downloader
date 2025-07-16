#!/bin/bash

# Auto-cleanup script for old downloaded files (older than 5 min)
# Place this in project root and make sure it has execute permission

DOWNLOAD_DIR="./downloads"

# Ensure the downloads folder exists
mkdir -p "$DOWNLOAD_DIR"

# Find and delete files older than 5 minutes
find "$DOWNLOAD_DIR" -type f -mmin +5 -exec rm -f {} \;

echo "🗑️  Cleanup complete: Files older than 5 minutes removed."
