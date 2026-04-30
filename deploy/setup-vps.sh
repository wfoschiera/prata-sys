#!/usr/bin/env bash
# setup-vps.sh - one-time VPS bootstrap for prata-sys
# Run as root or with sudo on a fresh Ubuntu VPS
#
# Usage: sudo bash setup-vps.sh
set -euo pipefail

echo "=== prata-sys VPS setup ==="

# --- System update ---
echo "--- Updating system packages ---"
apt update && apt upgrade -y
apt install -y curl wget unzip rsync ufw

# --- Create application user ---
echo "--- Creating 'prata' system user ---"
if ! id "prata" &>/dev/null; then
    useradd --system --create-home --shell /bin/bash prata
    echo "User 'prata' created"
else
    echo "User 'prata' already exists"
fi

# --- Install Python 3.14 via deadsnakes PPA ---
echo "--- Installing Python 3.14 ---"
apt install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt update
apt install -y python3.14 python3.14-venv python3.14-dev

# --- Install uv ---
echo "--- Installing uv ---"
if ! command -v uv &>/dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Make uv available system-wide
    cp /root/.local/bin/uv /usr/local/bin/uv
    cp /root/.local/bin/uvx /usr/local/bin/uvx
    echo "uv installed"
else
    echo "uv already installed"
fi

# --- Install Caddy ---
echo "--- Installing Caddy ---"
if ! command -v caddy &>/dev/null; then
    apt install -y debian-keyring debian-archive-keyring apt-transport-https
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
        | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
        | tee /etc/apt/sources.list.d/caddy-stable.list
    apt update
    apt install -y caddy
    echo "Caddy installed"
else
    echo "Caddy already installed"
fi

# --- Create directory structure ---
echo "--- Creating directory structure ---"
mkdir -p /opt/prata-sys/backend
mkdir -p /opt/prata-sys/deploy
mkdir -p /var/www/prata-sys/frontend

# Create placeholder index so Caddy has something to serve
if [ ! -f /var/www/prata-sys/frontend/index.html ]; then
    echo '<html><body><h1>prata-sys - deploy pending</h1></body></html>' \
        > /var/www/prata-sys/frontend/index.html
fi

chown -R prata:prata /opt/prata-sys
chown -R prata:prata /var/www/prata-sys

# --- Setup swap (1GB) ---
echo "--- Setting up 1GB swap ---"
if [ ! -f /swapfile ]; then
    fallocate -l 1G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "Swap enabled"
else
    echo "Swap already exists"
fi

# --- Configure sudoers for deploy user ---
echo "--- Configuring sudoers for prata user ---"
cat > /etc/sudoers.d/prata-deploy << 'EOF'
# Allow prata user to manage services without password (used by deploy.sh)
prata ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart prata-backend
prata ALL=(ALL) NOPASSWD: /usr/bin/systemctl reload caddy
prata ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart caddy
prata ALL=(ALL) NOPASSWD: /usr/bin/cp /opt/prata-sys/deploy/Caddyfile /etc/caddy/Caddyfile
prata ALL=(ALL) NOPASSWD: /usr/bin/cp /opt/prata-sys/deploy/prata-backend.service /etc/systemd/system/prata-backend.service
prata ALL=(ALL) NOPASSWD: /usr/bin/systemctl daemon-reload
EOF
chmod 440 /etc/sudoers.d/prata-deploy
echo "Sudoers configured"

# --- Firewall ---
echo "--- Configuring firewall ---"
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw --force enable
echo "Firewall configured"

# --- Enable Caddy ---
echo "--- Enabling Caddy ---"
systemctl enable caddy
systemctl start caddy || true

# --- Setup SSH directory for prata user ---
echo "--- Setting up SSH for prata user ---"
mkdir -p /home/prata/.ssh
chmod 700 /home/prata/.ssh
touch /home/prata/.ssh/authorized_keys
chmod 600 /home/prata/.ssh/authorized_keys
chown -R prata:prata /home/prata/.ssh

echo ""
echo "============================================="
echo "  VPS setup complete!"
echo "============================================="
echo ""
echo "Next steps:"
echo ""
echo "  1. Create the production .env file:"
echo "     sudo cp /opt/prata-sys/deploy/.env.example /opt/prata-sys/.env"
echo "     sudo nano /opt/prata-sys/.env"
echo "     sudo chown prata:prata /opt/prata-sys/.env"
echo "     sudo chmod 600 /opt/prata-sys/.env"
echo ""
echo "  2. Generate an SSH deploy key:"
echo "     ssh-keygen -t ed25519 -f /tmp/deploy_key -N ''"
echo "     cat /tmp/deploy_key.pub >> /home/prata/.ssh/authorized_keys"
echo "     echo 'Copy /tmp/deploy_key content to GitHub Secret VPS_SSH_KEY'"
echo "     cat /tmp/deploy_key"
echo "     rm /tmp/deploy_key /tmp/deploy_key.pub"
echo ""
echo "  3. Configure GitHub Secrets:"
echo "     - VPS_HOST_STAGING     = <public IP of this VPS>"
echo "     - VPS_USER             = prata"
echo "     - VPS_SSH_KEY          = <content of deploy_key>"
echo "     - VITE_API_URL_STAGING = http://<public IP> (or https://staging.pratapocos.com.br later)"
echo ""
echo "  4. Push to main branch to trigger the first deploy"
echo ""
echo "  5. After first deploy completes, install the config files:"
echo "     sudo cp /opt/prata-sys/deploy/Caddyfile /etc/caddy/Caddyfile"
echo "     sudo cp /opt/prata-sys/deploy/prata-backend.service /etc/systemd/system/"
echo "     sudo systemctl daemon-reload"
echo "     sudo systemctl restart caddy"
echo "     sudo systemctl enable --now prata-backend"
echo ""
