# SSH Key Diagnostic and Fix Guide

Write-Host "=== SSH Key Diagnostic ===" -ForegroundColor Red
Write-Host ""

Write-Host "❌ SSH Connection Failed: Permission denied (publickey,password)" -ForegroundColor Red
Write-Host ""
Write-Host "This means your SSH keys are not properly configured. Here's how to fix it:" -ForegroundColor Yellow
Write-Host ""

Write-Host "=== STEP 1: Check Local SSH Keys ===" -ForegroundColor Green
if (Test-Path "$env:USERPROFILE\.ssh\id_rsa") {
    Write-Host "✅ Local private key exists: $env:USERPROFILE\.ssh\id_rsa" -ForegroundColor Green
} else {
    Write-Host "❌ No local private key found" -ForegroundColor Red
    Write-Host "Generate one with: ssh-keygen -t rsa -b 4096" -ForegroundColor Yellow
}

if (Test-Path "$env:USERPROFILE\.ssh\id_rsa.pub") {
    Write-Host "✅ Local public key exists: $env:USERPROFILE\.ssh\id_rsa.pub" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your public key content:" -ForegroundColor Cyan
    Get-Content "$env:USERPROFILE\.ssh\id_rsa.pub"
} else {
    Write-Host "❌ No local public key found" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== STEP 2: Fix Server Access ===" -ForegroundColor Green
Write-Host "You need to add your public key to the server. Options:" -ForegroundColor Yellow
Write-Host ""
Write-Host "Option A - If you have password access:" -ForegroundColor Cyan
Write-Host "1. ssh-copy-id vico@69.164.245.17" -ForegroundColor White
Write-Host ""
Write-Host "Option B - Manual method:" -ForegroundColor Cyan
Write-Host "1. Copy your public key (shown above)" -ForegroundColor White
Write-Host "2. Login to server with password: ssh vico@69.164.245.17" -ForegroundColor White
Write-Host "3. Run: mkdir -p ~/.ssh && chmod 700 ~/.ssh" -ForegroundColor White
Write-Host "4. Run: echo 'YOUR_PUBLIC_KEY' >> ~/.ssh/authorized_keys" -ForegroundColor White
Write-Host "5. Run: chmod 600 ~/.ssh/authorized_keys" -ForegroundColor White
Write-Host ""

Write-Host "=== STEP 3: GitHub Actions SSH Key ===" -ForegroundColor Green
Write-Host "For GitHub Actions, you need a separate key:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Generate GitHub Actions key:" -ForegroundColor Cyan
Write-Host "   ssh-keygen -t rsa -b 4096 -f github_actions_key -N ''" -ForegroundColor White
Write-Host ""
Write-Host "2. Add public key to server:" -ForegroundColor Cyan
Write-Host "   cat github_actions_key.pub | ssh vico@69.164.245.17 'cat >> ~/.ssh/authorized_keys'" -ForegroundColor White
Write-Host ""
Write-Host "3. Encode private key for GitHub:" -ForegroundColor Cyan
Write-Host "   [Convert]::ToBase64String([IO.File]::ReadAllBytes('github_actions_key'))" -ForegroundColor White
Write-Host ""
Write-Host "4. Add to GitHub Secrets:" -ForegroundColor Cyan
Write-Host "   https://github.com/Ssebaleke/betting_bot_prod/settings/secrets/actions" -ForegroundColor White
Write-Host "   - VPS_SSH_KEY: (base64 encoded private key)" -ForegroundColor White
Write-Host "   - VPS_HOST: 69.164.245.17" -ForegroundColor White
Write-Host "   - VPS_USER: vico" -ForegroundColor White
Write-Host ""

Write-Host "=== STEP 4: Test Connection ===" -ForegroundColor Green
Write-Host "After fixing, test with:" -ForegroundColor Yellow
Write-Host "ssh vico@69.164.245.17 'echo Connection successful'" -ForegroundColor White
Write-Host ""

Write-Host "=== Current Status ===" -ForegroundColor Red
Write-Host "❌ GitHub Actions will NOT work until SSH keys are fixed" -ForegroundColor Red
Write-Host "❌ Manual deployments will NOT work" -ForegroundColor Red
Write-Host "❌ Server access is blocked" -ForegroundColor Red