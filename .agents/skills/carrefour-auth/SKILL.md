---
name: carrefour-auth
description: Refreshes Carrefour API session tokens. Use this skill whenever the user mentions authentication failure, 403 Forbidden, Cloudflare blocking, or provides new session cookies for the Carrefour API. It handles creating the session file locally and deploying it to /var/lib/carrefour-api using sudo.
---

# Carrefour Auth Skill

This skill automates the process of updating the authentication session for the Carrefour Remote Shopping API.

## Workflow

When triggered, follow these steps:

### 1. Collect Session Data
If the user hasn't already provided the cookies, use the `browser` subagent to extract fresh cookies from `https://www.carrefour.fr`.
Required keys usually include:
- `FRONTONE_SESSION_ID`
- `FRONTONE_SESSID`
- `FRONTAL_STORE`
- `__cf_bm` (Cloudflare token)

### 2. Create Local Session File
Write the cookies to `carrefour_session.json` in the current working directory.

### 3. Deploy to System Directory
Use `sudo` to copy the file to the state directory used by the systemd service:
```bash
sudo cp carrefour_session.json /var/lib/carrefour-api/carrefour_session.json
```

### 4. Adjust Permissions
Ensure the file is readable by the dynamic user (systemd manages this mostly, but ensure basic readability):
```bash
sudo chmod 644 /var/lib/carrefour-api/carrefour_session.json
```

### 5. Restart the Service
Restart the API server to pick up the new session:
```bash
sudo systemctl restart carrefour-api.service
```

### 6. Verify
Check the service status and logs to ensure it started successfully with the new session:
```bash
systemctl status carrefour-api.service
```
