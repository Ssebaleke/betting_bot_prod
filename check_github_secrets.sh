#!/bin/bash
# GitHub Actions Secrets Verification Guide

echo "=== GitHub Actions Secrets Check ==="
echo "===================================="
echo ""
echo "To check if your GitHub Actions secrets are properly configured:"
echo ""
echo "1. Go to: https://github.com/Ssebaleke/betting_bot_prod/settings/secrets/actions"
echo ""
echo "2. Verify these secrets exist:"
echo "   - VPS_SSH_KEY (base64 encoded private key)"
echo "   - VPS_HOST (should be: 69.164.245.17)"
echo "   - VPS_USER (should be: vico)"
echo ""
echo "3. To generate/check the SSH key for GitHub Actions:"
echo ""

# Check if we can connect to the server
echo "Testing SSH connection to server..."
if ssh -o ConnectTimeout=10 -o BatchMode=yes vico@69.164.245.17 exit 2>/dev/null; then
    echo "✅ SSH connection successful"
    
    echo ""
    echo "4. To create a new SSH key for GitHub Actions:"
    echo "   ssh-keygen -t rsa -b 4096 -f github_actions_key -N ''"
    echo "   cat github_actions_key.pub >> ~/.ssh/authorized_keys  # (run on server)"
    echo "   base64 -w 0 github_actions_key  # (use this for VPS_SSH_KEY secret)"
    
else
    echo "❌ Cannot connect to server. Check:"
    echo "   - Server is running"
    echo "   - SSH service is active"
    echo "   - Your local SSH key is authorized"
fi

echo ""
echo "5. Test the workflow manually:"
echo "   - Go to Actions tab in GitHub"
echo "   - Click 'Deploy' workflow"
echo "   - Click 'Run workflow'"
echo ""
echo "6. Check workflow logs for any errors"