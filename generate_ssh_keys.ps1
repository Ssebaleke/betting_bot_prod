# Generate SSH Keys for Server Access and GitHub Actions

Write-Host "=== SSH Key Generation Script ===" -ForegroundColor Green
Write-Host ""

# Create .ssh directory if it doesn't exist
$sshDir = "$env:USERPROFILE\.ssh"
if (!(Test-Path $sshDir)) {
    New-Item -ItemType Directory -Path $sshDir -Force
    Write-Host "✅ Created .ssh directory: $sshDir" -ForegroundColor Green
}

Write-Host "=== STEP 1: Generate Personal SSH Key ===" -ForegroundColor Cyan
Write-Host ""

# Check if personal key already exists
if (Test-Path "$sshDir\id_rsa") {
    Write-Host "⚠️  Personal SSH key already exists at $sshDir\id_rsa" -ForegroundColor Yellow
    $overwrite = Read-Host "Do you want to overwrite it? (y/N)"
    if ($overwrite -ne "y" -and $overwrite -ne "Y") {
        Write-Host "Skipping personal key generation..." -ForegroundColor Yellow
    } else {
        Write-Host "Generating new personal SSH key..." -ForegroundColor Yellow
        ssh-keygen -t rsa -b 4096 -f "$sshDir\id_rsa" -N '""'
    }
} else {
    Write-Host "Generating personal SSH key..." -ForegroundColor Yellow
    ssh-keygen -t rsa -b 4096 -f "$sshDir\id_rsa" -N '""'
}

Write-Host ""
Write-Host "=== STEP 2: Generate GitHub Actions SSH Key ===" -ForegroundColor Cyan
Write-Host ""

$githubKeyPath = "$PWD\github_actions_key"
if (Test-Path $githubKeyPath) {
    Write-Host "⚠️  GitHub Actions key already exists" -ForegroundColor Yellow
    $overwrite = Read-Host "Do you want to overwrite it? (y/N)"
    if ($overwrite -ne "y" -and $overwrite -ne "Y") {
        Write-Host "Skipping GitHub Actions key generation..." -ForegroundColor Yellow
    } else {
        Write-Host "Generating new GitHub Actions SSH key..." -ForegroundColor Yellow
        ssh-keygen -t rsa -b 4096 -f $githubKeyPath -N '""'
    }
} else {
    Write-Host "Generating GitHub Actions SSH key..." -ForegroundColor Yellow
    ssh-keygen -t rsa -b 4096 -f $githubKeyPath -N '""'
}

Write-Host ""
Write-Host "=== GENERATED KEYS ===" -ForegroundColor Green
Write-Host ""

# Display personal public key
if (Test-Path "$sshDir\id_rsa.pub") {
    Write-Host "1. Your Personal Public Key:" -ForegroundColor Cyan
    Write-Host "   (Add this to server's ~/.ssh/authorized_keys)" -ForegroundColor Yellow
    Write-Host ""
    Get-Content "$sshDir\id_rsa.pub"
    Write-Host ""
}

# Display GitHub Actions public key
if (Test-Path "$githubKeyPath.pub") {
    Write-Host "2. GitHub Actions Public Key:" -ForegroundColor Cyan
    Write-Host "   (Also add this to server's ~/.ssh/authorized_keys)" -ForegroundColor Yellow
    Write-Host ""
    Get-Content "$githubKeyPath.pub"
    Write-Host ""
}

# Generate base64 encoded private key for GitHub
if (Test-Path $githubKeyPath) {
    Write-Host "3. GitHub Actions Private Key (Base64 Encoded):" -ForegroundColor Cyan
    Write-Host "   (Use this for VPS_SSH_KEY secret in GitHub)" -ForegroundColor Yellow
    Write-Host ""
    $privateKeyBytes = [IO.File]::ReadAllBytes($githubKeyPath)
    $base64Key = [Convert]::ToBase64String($privateKeyBytes)
    Write-Host $base64Key -ForegroundColor White
    Write-Host ""
}

Write-Host "=== NEXT STEPS ===" -ForegroundColor Green
Write-Host ""
Write-Host "1. Add BOTH public keys to your server:" -ForegroundColor Yellow
Write-Host "   ssh vico@69.164.245.17" -ForegroundColor White
Write-Host "   mkdir -p ~/.ssh && chmod 700 ~/.ssh" -ForegroundColor White
Write-Host "   echo 'PASTE_PUBLIC_KEY_1_HERE' >> ~/.ssh/authorized_keys" -ForegroundColor White
Write-Host "   echo 'PASTE_PUBLIC_KEY_2_HERE' >> ~/.ssh/authorized_keys" -ForegroundColor White
Write-Host "   chmod 600 ~/.ssh/authorized_keys" -ForegroundColor White
Write-Host ""
Write-Host "2. Add GitHub Secrets:" -ForegroundColor Yellow
Write-Host "   Go to: https://github.com/Ssebaleke/betting_bot_prod/settings/secrets/actions" -ForegroundColor White
Write-Host "   - VPS_SSH_KEY: (the base64 encoded key above)" -ForegroundColor White
Write-Host "   - VPS_HOST: 69.164.245.17" -ForegroundColor White
Write-Host "   - VPS_USER: vico" -ForegroundColor White
Write-Host ""
Write-Host "3. Test connection:" -ForegroundColor Yellow
Write-Host "   ssh vico@69.164.245.17 'echo Connection successful'" -ForegroundColor White
Write-Host ""

# Save keys info to file for reference
$keyInfo = @"
=== SSH Keys Generated $(Get-Date) ===

Personal Public Key:
$(if (Test-Path "$sshDir\id_rsa.pub") { Get-Content "$sshDir\id_rsa.pub" })

GitHub Actions Public Key:
$(if (Test-Path "$githubKeyPath.pub") { Get-Content "$githubKeyPath.pub" })

GitHub Actions Private Key (Base64):
$(if (Test-Path $githubKeyPath) { 
    $privateKeyBytes = [IO.File]::ReadAllBytes($githubKeyPath)
    [Convert]::ToBase64String($privateKeyBytes)
})

Server Details:
- Host: 69.164.245.17
- User: vico
- Project: ~/betting_bot_prod

GitHub Secrets URL:
https://github.com/Ssebaleke/betting_bot_prod/settings/secrets/actions
"@

$keyInfo | Out-File -FilePath "ssh_keys_info.txt" -Encoding UTF8
Write-Host "✅ Key information saved to: ssh_keys_info.txt" -ForegroundColor Green