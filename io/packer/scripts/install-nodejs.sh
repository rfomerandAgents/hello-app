#!/bin/bash
set -e

echo "=== Installing Node.js ==="

# Install Node.js 18.x (LTS)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify installation
node --version
npm --version

echo "Node.js installation complete"
