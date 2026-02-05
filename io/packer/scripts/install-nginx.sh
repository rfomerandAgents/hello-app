#!/bin/bash
set -e

echo "=== Installing nginx ==="

# Install nginx
sudo apt-get install -y nginx

# Enable nginx service
sudo systemctl enable nginx
sudo systemctl start nginx

# Verify installation
nginx -v

echo "nginx installation complete"
