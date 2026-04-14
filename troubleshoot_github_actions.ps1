# GitHub Actions SSH Key Troubleshooting

Write-Host "=== GitHub Actions SSH Key Issue ===" -ForegroundColor Red
Write-Host ""
Write-Host "The error shows GitHub Actions can't authenticate with your server." -ForegroundColor Yellow
Write-Host "Let's troubleshoot this step by step." -ForegroundColor Yellow
Write-Host ""

Write-Host "1. Checking GitHub Actions Key Files..." -ForegroundColor Cyan
if (Test-Path "github_actions_key") {
    Write-Host "✅ Private key exists: github_actions_key" -ForegroundColor Green
    
    # Generate the base64 again to make sure it's correct
    Write-Host ""
    Write-Host "2. Regenerating Base64 Key for GitHub Secrets..." -ForegroundColor Cyan
    $privateKeyBytes = [IO.File]::ReadAllBytes("github_actions_key")
    $base64Key = [Convert]::ToBase64String($privateKeyBytes)
    
    Write-Host "✅ Base64 encoded key (copy this to VPS_SSH_KEY secret):" -ForegroundColor Green
    Write-Host $base64Key -ForegroundColor White
    Write-Host ""
    
} else {
    Write-Host "❌ GitHub Actions private key not found!" -ForegroundColor Red
    Write-Host "Run the key generation script again." -ForegroundColor Yellow
}

if (Test-Path "github_actions_key.pub") {
    Write-Host "3. Checking Public Key..." -ForegroundColor Cyan
    Write-Host "✅ Public key exists: github_actions_key.pub" -ForegroundColor Green
    Write-Host ""
    Write-Host "Public key content (must be in server's ~/.ssh/authorized_keys):" -ForegroundColor Yellow
    Get-Content "github_actions_key.pub"
    Write-Host ""
} else {
    Write-Host "❌ GitHub Actions public key not found!" -ForegroundColor Red
}

Write-Host "4. Troubleshooting Steps..." -ForegroundColor Cyan
Write-Host ""
Write-Host "STEP A: Verify GitHub Secrets" -ForegroundColor Yellow
Write-Host "Go to: https://github.com/Ssebaleke/betting_bot_prod/settings/secrets/actions" -ForegroundColor White
Write-Host "Make sure these secrets exist with EXACT values:" -ForegroundColor White
Write-Host "- VPS_SSH_KEY: (the base64 key shown above)" -ForegroundColor Gray
Write-Host "- VPS_HOST: 69.164.245.17" -ForegroundColor Gray
Write-Host "- VPS_USER: vico" -ForegroundColor Gray
Write-Host ""

Write-Host "STEP B: Verify Server Has the Public Key" -ForegroundColor Yellow
Write-Host "SSH to your server and check:" -ForegroundColor White
Write-Host "ssh vico@69.164.245.17" -ForegroundColor Gray
Write-Host "cat ~/.ssh/authorized_keys" -ForegroundColor Gray
Write-Host "# Should contain the public key shown above" -ForegroundColor Gray
Write-Host ""

Write-Host "STEP C: Test the Key Manually" -ForegroundColor Yellow
Write-Host "Test if the key works locally:" -ForegroundColor White
Write-Host "ssh -i github_actions_key vico@69.164.245.17 'echo Test successful'" -ForegroundColor Gray
Write-Host ""

Write-Host "STEP D: Common Issues" -ForegroundColor Yellow
Write-Host "- Wrong base64 encoding in GitHub secrets" -ForegroundColor White
Write-Host "- Public key not properly added to server" -ForegroundColor White
Write-Host "- Wrong file permissions on server (~/.ssh should be 700, authorized_keys should be 600)" -ForegroundColor White
Write-Host "- Multiple keys in authorized_keys not properly separated" -ForegroundColor White
Write-Host ""

Write-Host "=== Quick Fix Commands ===" -ForegroundColor Green
Write-Host "Run these on your server to fix permissions:" -ForegroundColor Yellow
Write-Host "chmod 700 ~/.ssh" -ForegroundColor Gray
Write-Host "chmod 600 ~/.ssh/authorized_keys" -ForegroundColor Gray
Write-Host ""

Write-Host "If the issue persists, the most likely cause is:" -ForegroundColor Red
Write-Host "❌ The base64 key in GitHub secrets doesn't match the private key" -ForegroundColor Red
Write-Host "❌ The public key isn't properly added to the server" -ForegroundColor Red