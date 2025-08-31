#!/bin/bash
export SUDO_PASSWORD="lab"
PROJECT_DIR="$(pwd)"

echo "lab" | sudo -S bash -c "cat > auto-deploy.sh << 'SCRIPT'
#!/bin/bash
set -e

export SUDO_PASSWORD=\"lab\"
PROJECT_DIR=\"\$(pwd)\"
LOG_FILE=\"\$PROJECT_DIR/deployment.log\"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e \"\${GREEN}[\$(date '+%H:%M:%S')]\${NC} \$1\" | tee -a \"\$LOG_FILE\"
}

run_sudo() {
    echo \"\$SUDO_PASSWORD\" | sudo -S \"\$@\"
}

install_dependencies() {
    log \"Installing dependencies...\"
    
    run_sudo apt update
    
    if ! command -v docker &> /dev/null; then
        run_sudo apt install -y docker.io docker-compose
        run_sudo systemctl start docker
        run_sudo usermod -aG docker \$USER
    fi
    
    run_sudo apt install -y python3 python3-pip python3-tk build-essential cmake git nodejs npm
    pip3 install --user requests
}

setup_project() {
    log \"Setting up project...\"
    
    run_sudo chown -R \$USER:\$USER .
    chmod +x build.sh start_all.sh stop_all.sh
    mkdir -p logs
    
    if [ -d \"web-interface\" ]; then
        cd web-interface && npm install && cd ..
    fi
}

build_deploy() {
    log \"Building system...\"
    
    ./build.sh
    
    if docker images | grep -q \"protection-relay\"; then
        log \"✓ Build successful\"
    else
        echo \"Build failed\"
        exit 1
    fi
}

main() {
    echo -e \"\${BLUE}Virtual Substation Auto-Deploy\${NC}\"
    echo \"==============================\"
    
    install_dependencies
    setup_project
    build_deploy
    
    echo -e \"\${GREEN}DEPLOYMENT COMPLETE!\${NC}\"
    echo \"\"
    echo \"Start: ./start_all.sh\"
    echo \"Stop:  ./stop_all.sh\"
}

main \"\$@\"
SCRIPT"

echo "lab" | sudo -S chown $USER:$USER auto-deploy.sh
chmod +x auto-deploy.sh
./auto-deploy.sh
