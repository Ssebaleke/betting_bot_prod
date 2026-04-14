# PowerShell script to check SSH keys and server configuration

Write-Host "=== Checking SSH Keys on Server ===" -ForegroundColor Green
Write-Host "Server: vico@69.164.245.17" -ForegroundColor Yellow
Write-Host ""

# Test SSH connection
Write-Host "Testing SSH connection..." -ForegroundColor Yellow
try {
    $sshTest = ssh -o ConnectTimeout=10 -o BatchMode=yes vico@69.164.245.17 "echo 'Connection successful'"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ SSH connection successful" -ForegroundColor Green
        
        Write-Host ""
        Write-Host "Checking authorized_keys on server..." -ForegroundColor Yellow
        ssh vico@69.164.245.17 @"
echo "1. Checking authorized_keys file:"
echo "=================================="
if [ -f ~/.ssh/authorized_keys ]; then
    echo "✅ authorized_keys exists"
    echo "Number of keys: `$(wc -l < ~/.ssh/authorized_keys)"
    echo ""
    echo "SSH directory permissions:"
    ls -la ~/.ssh/
    echo ""
    echo "Checking for GitHub Actions key..."
    if grep -q "github\|actions" ~/.ssh/authorized_keys 2>/dev/null; then
        echo "✅ Found GitHub Actions related key"
    else
        echo "❌ No GitHub Actions key found"
    fi
else
    echo "❌ No authorized_keys file found"
fi

echo ""
echo "2. Project directory status:"
echo "============================"
if [ -d ~/betting_bot_prod ]; then
    echo "✅ Project directory exists"
    cd ~/betting_bot_prod
    echo "Current branch: `$(git branch --show-current)"
    echo "Last commit: `$(git log --oneline -1)"
    echo "Git status:"
    git status --short
else
    echo "❌ Project directory not found"
fi

echo ""
echo "3. Docker status:"
echo "================"
docker-compose ps 2>/dev/null || echo "❌ Docker compose not running"
"@
        
    } else {
        Write-Host "❌ SSH connection failed" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error connecting to server: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== GitHub Actions Configuration ===" -ForegroundColor Green
Write-Host "Repository: https://github.com/Ssebaleke/betting_bot_prod" -ForegroundColor Yellow
Write-Host ""
Write-Host "Required secrets in GitHub:" -ForegroundColor Yellow
Write-Host "- VPS_SSH_KEY: Base64 encoded private key" -ForegroundColor White
Write-Host "- VPS_HOST: 69.164.245.17" -ForegroundColor White  
Write-Host "- VPS_USER: vico" -ForegroundColor White
Write-Host ""
Write-Host "Check secrets at: https://github.com/Ssebaleke/betting_bot_prod/settings/secrets/actions" -ForegroundColor Cyan