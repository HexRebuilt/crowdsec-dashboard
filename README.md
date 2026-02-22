# CrowdSec Dashboard

A modern, lightweight web dashboard for CrowdSec with Apple-inspired design, built with vanilla JavaScript and Flask.

## Features

- **Real-time monitoring** - Active bans, alerts, and event timeline
- **Smart notifications** - Apprise integration with threshold filtering and IP cooldowns
- **Apple-inspired UI** - Modern dark theme with smooth animations
- **Authentication** - Username/password or Auth0 SSO with password management
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

# Option 2: Auth0 (disables password login)
# AUTH0_DOMAIN=your-tenant.auth0.com
# AUTH0_CLIENT_ID=your_client_id
# AUTH0_CLIENT_SECRET=your_client_secret
```

### 3. Deploy with Docker Compose

```bash
docker compose up -d --build
```

Open http://localhost:5000

## Authentication

The dashboard supports two authentication methods:

### Username/Password

Set `AUTH_USERNAME` and `AUTH_PASSWORD` in your `.env` file. Users can change their password from the Settings tab.

### Auth0 SSO

When Auth0 is configured, password login is automatically disabled. Users authenticate via Auth0's hosted login page.

To set up Auth0:
1. Create a Single Page Application in Auth0
2. Add your domain to Allowed Callback URLs: `https://your-domain/callback`
3. Add your domain to Allowed Logout URLs and Allowed Web Origins
4. Set the environment variables in `.env`

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CROWDSEC_URL` | `http://crowdsec:8080` | CrowdSec LAPI URL |
| `CROWDSEC_API_KEY` | - | Bouncer API key (required) |
| `AUTH_USERNAME` | - | Login username |
| `AUTH_PASSWORD` | - | Login password |
| `AUTH0_DOMAIN` | - | Auth0 tenant domain |
| `AUTH0_CLIENT_ID` | - | Auth0 application client ID |
| `AUTH0_CLIENT_SECRET` | - | Auth0 application client secret |
| `APPRISE_API_URL` | - | External Apprise API URL |
| `APPRISE_API_KEY` | - | Apprise API authentication key |
| `APPRISE_CONFIG_KEY` | `crowdsec-dashboard` | Config key in Apprise API |
| `APPRISE_URLS` | - | Comma-separated Apprise URLs |
| `POLL_INTERVAL` | `30` | Seconds between polls |
| `NOTIFY_ON_BAN` | `true` | Send ban notifications |
| `NOTIFY_ON_ALERT` | `true` | Send alert notifications |
| `ALERT_THRESHOLD` | `5` | Minimum events for alert notification |
| `BAN_THRESHOLD` | `0` | Minimum events for ban notification |
| `NOTIFY_COOLDOWN` | `3600` | Seconds before re-notifying same IP |
| `DIGEST_INTERVAL` | `0` | Batch interval (0 = immediate) |
| `LOG_LEVEL` | `INFO` | Logging level |

## Project Structure

```
crowdsec-dashboard/
├── app.py                  # Flask backend with auth
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
| `GET` | `/api/alerts` | Recent alerts |
| `GET` | `/api/events` | Event timeline |
| `DELETE` | `/api/unban?id=N` | Remove decision |
| `GET` | `/api/apprise/status` | Apprise status |
| `POST` | `/api/apprise/urls` | Set Apprise URLs |
| `GET` | `/api/system/config` | Connection settings |
| `POST` | `/api/system/test` | Test connections |
| `GET` | `/health` | Health check |

## Decision Tooltips

The dashboard provides helpful tooltips for non-technical users:

- **Type**: Explains ban vs captcha vs throttle actions
- **Scenario**: Describes what attack pattern was detected
- **Origin**: Shows where the decision came from (CrowdSec, manual, lists)
- **Duration**: How long the block will remain active

## Apprise URLs

| Service | Format |
|---------|--------|
| Telegram | `tgram://TOKEN/CHAT_ID` |
| Discord | `discord://ID/TOKEN` |
| Gotify | `gotify://host/TOKEN` |
| ntfy | `ntfy://host/TOPIC` |
| Email | `mailto://user:pass@host` |

See [Apprise Wiki](https://github.com/caronc/apprise/wiki) for 80+ services.

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
python app.py
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
