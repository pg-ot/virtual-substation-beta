#!/bin/bash
# Development Environment Setup

echo "🔧 Setting up IEC 61850 Development Environment..."

# Initialize git submodules
git submodule update --init --recursive

# Install development dependencies
sudo apt update
sudo apt install -y build-essential cmake git python3-tk nodejs npm jq curl docker.io python3-distutils

# Install newer Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Setup Docker
sudo usermod -aG docker $USER
sudo systemctl start docker
sudo systemctl enable docker
newgrp docker

# Setup pre-commit hooks
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
make test-goose
EOF
chmod +x .git/hooks/pre-commit

# Create development aliases
cat >> ~/.bashrc << 'EOF'
alias vs-start='make start'
alias vs-stop='make stop'
alias vs-test='make test-goose'
alias vs-logs='docker-compose logs -f'
EOF

echo "✅ Development environment ready!"
echo "Run: source ~/.bashrc"