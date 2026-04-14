#!/bin/bash
# Check SSH keys and GitHub Actions setup on server

echo "=== Checking SSH Keys on Server ==="
ssh vico@69.164.245.17 << 'EOF'

echo "1. Checking authorized_keys file:"
echo "=================================="
if [ -f ~/.ssh/authorized_keys ]; then
    echo "✅ authorized_keys exists"
    echo "Number of keys: $(wc -l < ~/.ssh/authorized_keys)"
    echo ""
    echo "Key fingerprints:"
    while read -r key; do
        if [[ $key == ssh-* ]]; then
            echo "$key" | ssh-keygen -lf -
        fi
    done < ~/.ssh/authorized_keys
else
    echo "❌ No authorized_keys file found"
fi

echo ""
echo "2. Checking SSH directory permissions:"
echo "====================================="
ls -la ~/.ssh/

echo ""
echo "3. Checking if GitHub Actions key exists:"
echo "========================================"
if grep -q "github" ~/.ssh/authorized_keys 2>/dev/null; then
    echo "✅ Found GitHub-related key"
else
    echo "❌ No GitHub-related key found"
fi

echo ""
echo "4. Checking current user and home directory:"
echo "==========================================="
echo "Current user: $(whoami)"
echo "Home directory: $HOME"
echo "Working directory: $(pwd)"

echo ""
echo "5. Checking project directory:"
echo "============================="
if [ -d ~/betting_bot_prod ]; then
    echo "✅ Project directory exists"
    cd ~/betting_bot_prod
    echo "Git status:"
    git status --porcelain
    echo "Current branch: $(git branch --show-current)"
    echo "Last commit: $(git log --oneline -1)"
else
    echo "❌ Project directory not found"
fi

echo ""
echo "6. Checking Docker status:"
echo "========================="
docker-compose ps 2>/dev/null || echo "❌ Docker compose not running or not found"

EOF

echo ""
echo "=== Local SSH Key Check ==="
echo "=========================="
if [ -f ~/.ssh/id_rsa.pub ]; then
    echo "✅ Local public key exists"
    echo "Fingerprint:"
    ssh-keygen -lf ~/.ssh/id_rsa.pub
else
    echo "❌ No local SSH key found"
fi