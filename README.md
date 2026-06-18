# CrowdSec Dashboard

A modern, lightweight web dashboard for CrowdSec with Apple-inspired design, built with vanilla JavaScript and Flask.

## Features

- **Real-time monitoring** - Active bans, actionable alarms, and event timeline
- **Smart notifications** - Apprise integration with threshold filtering and IP cooldowns
- **Apple-inspired UI** - Modern dark/light theme with smooth animations and automatic browser/system preference detection
- **Authentication** - Username/password or OIDC SSO (Auth0, Authentik, etc.) with password management
- **Tooltips** - Helpful explanations for non-technical users
- **API or Embedded mode** - Use external Apprise API or built-in notifications
- **Connection management** - Test and monitor connections from UI
- **One-click unban** - Remove decisions directly from dashboard

## Quick Start

### 1. Get CrowdSec API Key

```bash
docker exec crowdsec cscli bouncers add crowdsec-dashboard
```

Copy the generated API key.

### 2. Create Environment File

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# CrowdSec Configuration
CROWDSEC_API_KEY=your_api_key_here

# Authentication (choose one)
# Option 1: Username/Password
AUTH_USERNAME=admin
AUTH_PASSWORD=your_secure_password

# Option 2: OIDC SSO (Auth0, Authentik, etc.)
# AUTH0_DOMAIN=your-tenant.auth0.com
# AUTH0_CLIENT_ID=your_client_id
# AUTH0_CLIENT_SECRET=your_client_secret
# APP_URL=https://your-dashboard.example.com
```

### 3. Deploy with Docker Compose

```bash
docker compose up -d --build
```

Open http://localhost:5000

## Deployment Notes

### Same Machine (Default)

By default, this container is designed to run on the same machine as CrowdSec. The `CROWDSEC_URL` defaults to `http://crowdsec:8080`, which works when both containers are in the same Docker network.

### Different Machine

If running on a different machine, set `CROWDSEC_URL` to the CrowdSec LAPI address:

```env
CROWDSEC_URL=http://your-crowdsec-host:8080
```

## Authentication

The dashboard supports two authentication methods:

### Username/Password

Set `AUTH_USERNAME` and `AUTH_PASSWORD` in your `.env` file. Users can change their password from the Settings tab.

### OIDC SSO (Auth0, Authentik, etc.)

When OIDC is configured, password login is automatically disabled. Users authenticate via the SSO provider.

To set up OIDC:
1. Create an application in your OIDC provider (Auth0, Authentik, Keycloak, etc.)
2. Add your domain to Redirect URIs: `https://your-domain/callback`
3. Set the environment variables in `.env`:
   - `AUTH0_DOMAIN` - The OIDC issuer URL or Auth0 tenant domain
   - `AUTH0_CLIENT_ID` - Application client ID
   - `AUTH0_CLIENT_SECRET` - Application client secret
   - `APP_URL` - Your dashboard's public URL (required for callback)

#### Authentik Example

```env
AUTH0_DOMAIN=https://auth.example.com/application/o/your-app/.well-known/openid-configuration
AUTH0_CLIENT_ID=your_client_id
AUTH0_CLIENT_SECRET=your_client_secret
APP_URL=https://crowdsec.example.com
```

In Authentik, add Redirect URI: `https://crowdsec.example.com/callback`

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CROWDSEC_URL` | `http://crowdsec:8080` | CrowdSec LAPI URL (change if not on same machine) |
| `CROWDSEC_API_KEY` | - | Bouncer API key (required) |
| `AUTH_USERNAME` | - | Login username |
| `AUTH_PASSWORD` | - | Login password |
| `AUTH_SECRET_KEY` | (random) | Session signing key |
| `AUTH0_DOMAIN` | - | OIDC issuer URL or Auth0 tenant domain |
| `AUTH0_CLIENT_ID` | - | OIDC application client ID |
| `AUTH0_CLIENT_SECRET` | - | OIDC application client secret |
| `APP_URL` | - | Dashboard public URL (required for OIDC callback) |
| `APPRISE_API_URL` | - | External Apprise API URL |
| `APPRISE_API_KEY` | - | Apprise API Bearer token (if required) |
| `APPRISE_CONFIG_KEY` | `crowdsec-dashboard` | Configuration storage key in Apprise API |
| `APPRISE_CONFIG_URL` | - | Remote config URL to fetch Apprise URLs |
| `APPRISE_URLS` | - | Comma-separated Apprise URLs (for embedded mode) |
| `POLL_INTERVAL` | `30` | Seconds between polls |
| `NOTIFY_ON_BAN` | `true` | Send ban notifications |
| `NOTIFY_ON_ALERT` | `true` | Send alert notifications |
| `ALERT_THRESHOLD` | `5` | Minimum events for alert notification |
| `BAN_THRESHOLD` | `0` | Minimum events for ban notification |
| `NOTIFY_COOLDOWN` | `3600` | Seconds before re-notifying same IP |
| `DIGEST_INTERVAL` | `0` | Batch interval (0 = immediate) |
| `LOG_LEVEL` | `INFO` | Logging level |
| `UNSECURE` | `false` | Disable authentication (not recommended) |

## Alerts vs Alarms

The dashboard distinguishes between two concepts:

- **Alerts** (internal): Raw security events detected by CrowdSec. These are fetched automatically but not displayed in a separate tab since they can be voluminous and require interpretation.

- **Alarms** (displayed): Actionable items derived from alerts and other data sources. The Alarms tab shows security issues that require attention, including:
  - New attack sources detected
  - Alerts near threshold needing manual review
  - Failed login patterns
  - API connection errors
  - Geo-anomalies
  - Rate limit warnings
  - Whitelist expiry warnings

This design keeps the interface focused on actionable items rather than raw data.

## Project Structure

```
crowdsec-dashboard/
├── main.py                 # Flask backend with auth (renamed from app.py)
├── static/
│   ├── index.html          # Main HTML with login overlay
│   ├── app.js              # Frontend logic with auth
│   └── style.css           # Apple-style dark theme
├── Dockerfile              # Python slim image
├── docker-compose.yml      # Container orchestration
├── .env.example            # Environment template
├── requirements.txt        # Python dependencies
├── PLAN.md                 # Development roadmap
└── README.md               # This file
```

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/auth/status` | Check auth configuration |
| `POST` | `/api/auth/login` | Login with credentials or Auth0 |
| `POST` | `/api/auth/logout` | End session |
| `GET` | `/api/auth/check` | Verify authentication |
| `POST` | `/api/auth/password` | Change password (credentials only) |

### Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/status` | System status and counters |
| `GET` | `/api/config` | Runtime configuration |
| `PATCH` | `/api/config` | Update configuration |
| `GET` | `/api/decisions` | Active bans |
| `GET` | `/api/alarms` | Actionable alarms requiring attention |
| `GET` | `/api/events` | Event timeline |
| `DELETE` | `/api/unban?id=N` | Remove decision |
| `GET` | `/api/apprise/status` | Apprise status |
| `POST` | `/api/apprise/urls` | Set Apprise URLs |
| `GET` | `/api/system/config` | Connection settings |
| `POST` | `/api/system/test` | Test connections |
| `GET` | `/health` | Health check |

## Decision Tooltips

The dashboard provides helpful tooltips for non-technical users:

- **Scenario**: Describes what attack pattern was detected
- **When**: When the ban was created (relative time)

## Theme

The dashboard supports both dark and light themes:

- **Automatic mode**: By default, the theme follows your system preference
- **Manual toggle**: Click the sun/moon icon in the header or login page to override
- **Persistence**: Your manual choice is saved in localStorage

## Apprise URLs

| Service | Format |
|---------|--------|
| Telegram | `tgram://TOKEN/CHAT_ID` |
| Discord | `discord://ID/TOKEN` |
| Gotify | `gotify://host/TOKEN` |
| ntfy | `ntfy://host/TOPIC` |
| Email | `mailto://user:pass@host` |

See [Apprise Wiki](https://github.com/caronc/apprise/wiki) for 80+ services.

### Apprise API Configuration

For managing multiple notification services, use an external Apprise API instance:

```env
APPRISE_API_URL=https://apprise.example.com
APPRISE_CONFIG_KEY=crowdsec-dashboard
```

1. Set up [Apprise API](https://github.com/caronc/apprise-api)
2. Configure your notification URLs in the Apprise UI under the config key `crowdsec-dashboard`
3. The dashboard will automatically use this configuration for notifications

### Apprise Config URL

Alternatively, you can fetch notification URLs from a remote config URL:

```env
APPRISE_CONFIG_URL=https://apprise.example.com/cfg/your-config-hash
```

The URL should return JSON in one of these formats:
- `["url1", "url2"]` - Array of URLs
- `{"urls": ["url1", "url2"]}` - Object with urls key
- `{"url": "single-url"}` - Single URL object

## Development

### Prerequisites

- Python 3.12+
- Docker (for deployment)

### Local Development

```bash
# Install backend dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Run backend
python main.py
```

Open http://localhost:5000

### Build Docker Image

```bash
docker build -t crowdsec-dashboard .
```

## Security Notes

- Passwords are stored in a file (`/app/.auth_password`) when changed at runtime
- Sessions use HTTP-only cookies with 24-hour expiry
- Auth0 integration disables password-based login
- `.env` file should never be committed to version control

## License

MIT
