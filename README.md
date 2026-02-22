# CrowdSec Dashboard

A modern, lightweight web dashboard for CrowdSec built with Svelte 5 and Flask.

## Features

- **Real-time monitoring** - Active bans, alerts, and event timeline
- **Smart notifications** - Apprise integration with threshold filtering and IP cooldowns
- **Modern UI** - Apple-inspired design with Svelte 5
- **API or Embedded mode** - Use external Apprise API or built-in notifications
- **Connection management** - Test and monitor connections from UI
- **One-click unban** - Remove decisions directly from dashboard

## Quick Start

### 1. Get CrowdSec API Key

```bash
docker exec crowdsec cscli bouncers add crowdsec-dashboard
```

Copy the generated API key.

### 2. Deploy with Docker Compose

Add to your existing `docker-compose.yml`:

```yaml
services:
  crowdsec-dashboard:
    build:
      context: .
    container_name: crowdsec-dashboard
    restart: unless-stopped
    networks:
      - traefik-cloudflare-tunnel_default
      - apprise_default
    environment:
      CROWDSEC_URL: http://crowdsec:8080
      CROWDSEC_API_KEY: "YOUR_API_KEY"
      APPRISE_API_URL: "http://apprise:8000"
      UNSECURE: "true"
    ports:
      - "5000:5000"

networks:
  traefik-cloudflare-tunnel_default:
    external: true
  apprise_default:
    external: true
```

### 3. Build and Run

```bash
docker compose up -d --build crowdsec-dashboard
```

Open http://localhost:5000

## Development

### Prerequisites

- Node.js 20+
- Python 3.12+

### Setup

```bash
# Install frontend dependencies
npm install

# Install backend dependencies
pip install -r requirements.txt

# Run development server (frontend + backend proxy)
npm run dev

# In another terminal, run backend
python app.py
```

### Build

```bash
# Build frontend only
npm run build

# Build Docker image
docker build -t crowdsec-dashboard .
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CROWDSEC_URL` | `http://crowdsec:8080` | CrowdSec LAPI URL |
| `CROWDSEC_API_KEY` | - | Bouncer API key (required) |
| `APPRISE_API_URL` | - | External Apprise API URL |
| `APPRISE_API_KEY` | - | Apprise API authentication key |
| `APPRISE_CONFIG_KEY` | `crowdsec-dashboard` | Config key in Apprise API |
| `APPRISE_URLS` | - | Comma-separated Apprise URLs (embedded mode) |
| `POLL_INTERVAL` | `30` | Seconds between polls |
| `NOTIFY_ON_BAN` | `true` | Send ban notifications |
| `NOTIFY_ON_ALERT` | `true` | Send alert notifications |
| `ALERT_THRESHOLD` | `5` | Minimum events for alert notification |
| `BAN_THRESHOLD` | `0` | Minimum events for ban notification |
| `NOTIFY_COOLDOWN` | `3600` | Seconds before re-notifying same IP |
| `DIGEST_INTERVAL` | `0` | Batch interval (0 = immediate) |
| `UNSECURE` | `false` | Allow direct port access |
| `LOG_LEVEL` | `INFO` | Logging level |

## Project Structure

```
crowdsec-dashboard/
├── src/                    # Svelte frontend source
│   ├── components/         # UI components
│   ├── lib/                # API client and stores
│   ├── App.svelte          # Main app component
│   ├── app.css             # Global styles
│   ├── main.js             # Entry point
│   └── index.html          # HTML template
├── static/                 # Built frontend (generated)
├── public/                 # Static assets
├── app.py                  # Flask backend
├── requirements.txt        # Python dependencies
├── package.json            # Node.js dependencies
├── vite.config.js          # Vite configuration
├── svelte.config.js        # Svelte configuration
├── Dockerfile              # Multi-stage Docker build
└── docker-compose.yml      # Docker Compose config
```

## API Endpoints

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

## Apprise URLs

| Service | Format |
|---------|--------|
| Telegram | `tgram://TOKEN/CHAT_ID` |
| Discord | `discord://ID/TOKEN` |
| Gotify | `gotify://host/TOKEN` |
| ntfy | `ntfy://host/TOPIC` |
| Email | `mailto://user:pass@host` |

See [Apprise Wiki](https://github.com/caronc/apprise/wiki) for 80+ services.

## License

MIT
