# Test SSH Connection and GitHub Actions Setup

Write-Host "=== Testing SSH Connection and GitHub Actions Setup ===" -ForegroundColor Green
Write-Host ""

# Test SSH connection
Write-Host "1. Testing SSH Connection to Server..." -ForegroundColor Cyan
Write-Host "   Server: vico@69.164.245.17" -ForegroundColor Yellow
Write-Host ""

try {
    $sshTest = ssh -o ConnectTimeout=10 vico@69.164.245.17 "echo 'SSH Connection Successful'"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ SSH Connection: SUCCESS" -ForegroundColor Green
        Write-Host "   Output: $sshTest" -ForegroundColor White
        
        Write-Host ""
        Write-Host "2. Checking Server Environment..." -ForegroundColor Cyan
        
        # Check server details
        ssh vico@69.164.245.17 @"
echo "=== Server Information ==="
echo "Current user: `$(whoami)"
echo "Home directory: `$HOME"
echo "Current time: `$(date)"
echo ""

echo "=== Project Status ==="
if [ -d ~/betting_bot_prod ]; then
    echo "✅ Project directory exists"
    cd ~/betting_bot_prod
    echo "Current branch: `$(git branch --show-current)"
    echo "Last commit: `$(git log --oneline -1)"
    echo "Git status:"
    git status --short
    echo ""
    
    echo "=== Docker Status ==="
    if command -v docker-compose >/dev/null 2>&1; then
        echo "✅ Docker Compose available"
        docker-compose ps 2>/dev/null || echo "⚠️  No containers running"
    else
        echo "❌ Docker Compose not found"
    fi
else
    echo "❌ Project directory not found at ~/betting_bot_prod"
fi

echo ""
echo "=== SSH Keys Check ==="
if [ -f ~/.ssh/authorized_keys ]; then
    echo "✅ authorized_keys exists"
    echo "Number of keys: `$(wc -l < ~/.ssh/authorized_keys)"
    echo "Key types:"
    grep -o "ssh-[a-z]*" ~/.ssh/authorized_keys | sort | uniq -c
else
    echo "❌ No authorized_keys file"
fi
"@
        
    } else {
        Write-Host "❌ SSH Connection: FAILED" -ForegroundColor Red
        Write-Host "   Error code: $LASTEXITCODE" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ SSH Connection: ERROR" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "3. GitHub Actions Readiness Check..." -ForegroundColor Cyan

# Check if GitHub Actions key exists
if (Test-Path "github_actions_key") {
    Write-Host "✅ GitHub Actions private key exists" -ForegroundColor Green
} else {
    Write-Host "❌ GitHub Actions private key missing" -ForegroundColor Red
}

if (Test-Path "github_actions_key.pub") {
    Write-Host "✅ GitHub Actions public key exists" -ForegroundColor Green
} else {
    Write-Host "❌ GitHub Actions public key missing" -ForegroundColor Red
}

Write-Host ""
Write-Host "4. Next Steps for GitHub Actions..." -ForegroundColor Cyan
Write-Host ""
Write-Host "To verify GitHub Actions secrets are configured:" -ForegroundColor Yellow
Write-Host "1. Go to: https://github.com/Ssebaleke/betting_bot_prod/settings/secrets/actions" -ForegroundColor White
Write-Host "2. Verify these secrets exist:" -ForegroundColor White
Write-Host "   - VPS_SSH_KEY" -ForegroundColor White
Write-Host "   - VPS_HOST" -ForegroundColor White
Write-Host "   - VPS_USER" -ForegroundColor White
Write-Host ""
Write-Host "To test GitHub Actions:" -ForegroundColor Yellow
Write-Host "1. Make a small change and commit:" -ForegroundColor White
Write-Host "   git add ." -ForegroundColor Gray
Write-Host "   git commit -m 'Test deployment'" -ForegroundColor Gray
Write-Host "   git push origin main" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Or trigger manually:" -ForegroundColor White
Write-Host "   Go to Actions tab → Deploy workflow → Run workflow" -ForegroundColor Gray
Write-Host ""

Write-Host "=== Summary ===" -ForegroundColor Green
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ SSH connection is working" -ForegroundColor Green
    Write-Host "✅ Server is accessible" -ForegroundColor Green
    Write-Host "✅ Ready for GitHub Actions deployment" -ForegroundColor Green
    Write-Host ""
    Write-Host "🚀 Your GitHub Actions should now work!" -ForegroundColor Green
} else {
    Write-Host "❌ There are still issues to resolve" -ForegroundColor Red
    Write-Host "   Check the error messages above" -ForegroundColor Yellow
}