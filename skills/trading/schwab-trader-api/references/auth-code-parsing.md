# Auth Code Parsing

## Problem
When Schwab redirects to your `redirect_uri`, the URL contains the auth code plus a session parameter:

```
https://127.0.0.1:8080/?code=C0.b2F1dGgyLmJkYy5zY2h3YWIuY29t.XxhTuYGvRtmb2s1kq7PNmcG49i3hkQHFHGhSas2a58A%40&session=9fc517a1-bb39-44b0-80ab-567815c532fd
```

If you send the full `code=...&session=...` to the token endpoint, you get:
```json
{"error":"unsupported_token_type","error_description":"Authorization code is invalid, expired or revoked"}
```

## Fix
Strip everything after `&` before exchanging the code:

```python
raw = input("Enter the authorization code: ").strip()

# Handle full URL paste
if 'code=' in raw:
    if raw.startswith('http'):
        query = urllib.parse.urlparse(raw).query
    else:
        query = raw.split('?')[-1]
    params = urllib.parse.parse_qs(query)
    code = params.get('code', [''])[0]
else:
    # Raw code with trailing &session=...
    code = raw.split('&')[0].strip()
```

## Why This Happens
The `session` parameter is for Schwab's tracking, not part of the auth code. The token endpoint only expects the code itself.
