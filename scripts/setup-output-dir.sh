#!/bin/bash

# FFmpeg API Output Directory Setup Script
# This script helps setup /output directory with correct permissions

set -e

OUTPUT_DIR="${1:-.}/output"
USER_ID="${2:-1000}"
GROUP_ID="${3:-1000}"

echo "=========================================="
echo "FFmpeg API Output Directory Setup"
echo "=========================================="
echo ""
echo "Output Directory: $OUTPUT_DIR"
echo "User ID: $USER_ID"
echo "Group ID: $GROUP_ID"
echo ""

# Create directory if it doesn't exist
echo "[1/4] Creating output directory..."
if [ -d "$OUTPUT_DIR" ]; then
    echo "  ✓ Directory already exists: $OUTPUT_DIR"
else
    mkdir -p "$OUTPUT_DIR"
    echo "  ✓ Created directory: $OUTPUT_DIR"
fi

# Set permissions
echo "[2/4] Setting permissions (755)..."
chmod 755 "$OUTPUT_DIR"
echo "  ✓ Permissions set to 755"

# Set ownership (if running as root)
echo "[3/4] Setting ownership..."
if [ "$(id -u)" = "0" ]; then
    chown "$USER_ID:$GROUP_ID" "$OUTPUT_DIR"
    echo "  ✓ Owner set to $USER_ID:$GROUP_ID"
else
    echo "  ℹ Skipped (not running as root)"
fi

# Verify permissions
echo "[4/4] Verifying setup..."
if [ -w "$OUTPUT_DIR" ]; then
    echo "  ✓ Directory is writable"
else
    echo "  ✗ Directory is NOT writable"
    exit 1
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Directory Info:"
ls -ld "$OUTPUT_DIR"
echo ""
echo "Test write access:"
TEST_FILE="$OUTPUT_DIR/.setup_test_$(date +%s).txt"
if echo "test" > "$TEST_FILE" && rm "$TEST_FILE"; then
    echo "  ✓ Write test successful"
else
    echo "  ✗ Write test failed"
    exit 1
fi

echo ""
echo "Ready to run the service!"
