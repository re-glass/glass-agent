# Schwab API Authentication Guide

## Overview

Schwab's official API uses OAuth2 for authentication. This reference covers setup, common issues, and workarounds.

## Initial Setup

1. Go to https://developer.schwab.com/
2. Create a new app with:
   - **App Name**: Descriptive name for your reference
   - **Redirect URI**: `http://localhost:8080` (or `https://localhost:8080`)
   - **Scopes**: MarketData, AccountAccess, Trade, Orders
3. Save the **App Key** (Client ID) and **App Secret** (Client Secret)

## OAuth2 Flow

### Standard Flow
1. Browser opens to Schwab login
2. User authenticates and authorizes the app
3. Schwab redirects to `http://localhost:8080?code=AUTH_CODE`
4. Bot captures the code and exchanges it for access/refresh tokens

### Manual Fallback
If the redirect URI fails or localhost isn't accessible:
1. Bot prints the authorization URL
2. User opens it manually in browser
3. After auth, browser shows a URL with `?code=...`
4. User copies the code and pastes it into the terminal

## PAT Authentication (Alternative)

When browser auth is problematic, use a GitHub-style Personal Access Token approach:

1. Generate token at https://github.com/settings/tokens (classic)
2. Store securely (e.g., `~/.git-credentials` or environment variable)
3. Use for API calls or git operations

### Git Remote with PAT
```bash
git remote set-url origin https://oauth2:TOKEN@github.com/user/repo.git
```

## Common Issues

| Problem | Solution |
|---------|----------|
| "Invalid redirect URI" | Use `https://localhost:8080` or manual code fallback |
| "Resource not accessible by PAT" | Token lacks required scope — regenerate with correct scopes |
| Token expires | Refresh token flow (automatic in bot) |
| SSH key fails | Use HTTPS with PAT instead |

## Rate Limits

- Typically 120 requests/minute
- Check current docs at developer.schwab.com
- Implement exponential backoff in bot code
