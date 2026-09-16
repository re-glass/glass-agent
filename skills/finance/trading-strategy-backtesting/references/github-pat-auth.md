# GitHub Authentication for Bot Code Storage

## Overview

When saving trading bot code to GitHub, you need to authenticate the `gh` CLI. This can be tricky on headless servers.

## Authentication Methods

### Method 1: Device Code (Interactive)
```bash
gh auth login --git-protocol https --web
```
- Provides a one-time code
- User goes to https://github.com/login/device
- Works in browsers but can time out on CLI

### Method 2: Personal Access Token (Recommended for servers)
```bash
echo "YOUR_PAT" | gh auth login --with-token
```
- More reliable on headless systems
- Doesn't require browser interaction

## PAT Creation

1. Go to https://github.com/settings/tokens
2. Click **Generate new token (classic)**
3. **Scopes needed:**
   - `repo` — full repo access (for private repos)
   - `public_repo` — if repo can be public
4. Generate and copy immediately

## PAT Type Matters

| Type | `repo` Scope? | Works with `gh`? |
|------|---------------|------------------|
| **Classic** | ✅ Yes | ✅ Yes |
| **Fine-grained** | ❌ Limited | ❌ Often fails |

**Fine-grained tokens** often fail with `gh repo create` (403 "Resource not accessible"). Use **classic tokens** for full repo creation and push access.

## Pushing Existing Code

```bash
# Initialize
cd /path/to/project
git init
git add -A
git commit -m "Initial commit"

# Create repo (via API if gh fails)
curl -s -H "Authorization: token YOUR_PAT" \
  -H "Accept: application/vnd.github.v3+json" \
  -X POST https://api.github.com/user/repos \
  -d '{"name":"repo-name","description":"..."}'

# Push
git remote add origin https://github.com/USER/REPO.git
git branch -M main
git push -u origin main
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `gh auth status` shows not logged in | Re-run `gh auth login --with-token` |
| `403 Resource not accessible` on repo create | Use classic PAT, not fine-grained |
| Token in command history | Use `<<<` (herestring) or pipe |
| `gh repo create` fails | Create repo manually on github.com, then push |

## Security Notes

- Never commit tokens to the repo
- Add `tokens.json` and `.env` to `.gitignore`
- Use `chmod 600` on token files
- Rotate PATs periodically
