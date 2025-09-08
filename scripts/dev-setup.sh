#!/bin/bash
# Development Environment Setup

echo "🔧 Setting up IEC 61850 Development Environment..."

# Install development dependencies
sudo apt update
sudo apt install -y build-essential cmake git python3-tk nodejs npm jq curl docker.io docker-compose

# Setup Docker
sudo usermod -aG docker $USER
sudo systemctl start docker
sudo systemctl enable docker

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
echo "⚠️  Log out and back in (or run 'newgrp docker') for Docker permissions"
echo "Run: source ~/.bashrc"