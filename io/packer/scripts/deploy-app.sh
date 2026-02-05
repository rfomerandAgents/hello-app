#!/bin/bash
set -e

echo "=== Deploying application ==="

# Example deployment script
# Customize for your application

# Create web root
sudo mkdir -p /var/www/html

# Copy application files
sudo cp -r /tmp/app/* /var/www/html/

# Set permissions
sudo chown -R www-data:www-data /var/www/html
sudo chmod -R 755 /var/www/html

# Configure nginx
sudo tee /etc/nginx/sites-available/default > /dev/null <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    root /var/www/html;
    index index.html;

    server_name _;

    location / {
        try_files \$uri \$uri/ =404;
    }
}
EOF

# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

echo "Application deployment complete"
