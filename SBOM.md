# CrowdSec Dashboard - Software Bill of Materials (SBOM)

**Project:** CrowdSec Dashboard  
**Version:** 1.0.2  
**Generated:** 2026-02-25

## Backend Components

| Component | Version | License | Description |
|-----------|---------|---------|-------------|
| Python | 3.12-slim | PSF-2.0 | Runtime environment |
| Flask | >= 3.0 | BSD-3-Clause | Web framework |
| Flask-CORS | >= 4.0 | MIT | CORS support for Flask |
| Requests | >= 2.31 | Apache-2.0 | HTTP client library |
| Apprise | >= 1.8 | BSD-3-Clause | Multi-notification service library (80+ services) |
| Requests-oauthlib | - | ISC | OAuth extension for requests |
| Markdown | >= 3.0 | BSD-3-Clause | Markdown parser |
| PyYAML | >= 6.0 | MIT | YAML parser |
| OAuthlib | - | BSD-3-Clause | OAuth implementation |
| itsdangerous | - | BSD-3-Clause | Data signing library |
| Jinja2 | - | BSD-3-Clause | Template engine |
| Werkzeug | - | BSD-3-Clause | WSGI utilities |
| Click | - | BSD-3-Clause | Command line toolkit |
| MarkupSafe | - | BSD-3-Clause | Safe string handling |
| Certifi | - | MPL-2.0 | CA certificate bundle |
| Charset-normalizer | - | MIT | Character encoding detection |
| IDNA | - | BSD-3-Clause | Internationalized domain names |
| Urllib3 | - | MIT | HTTP client |

## Frontend Components

| Component | Version | License | Source | Description |
|-----------|---------|---------|--------|-------------|
| Chart.js | 4.4.1 | MIT | CDN | Interactive pie charts |
| Vanilla JavaScript | ES6+ | - | Native | No framework dependencies |
| CSS3 | - | - | Custom | Apple-inspired dark theme |

## Docker Components

| Component | Base | Description |
|-----------|------|-------------|
| Dockerfile | python:3.12-slim | Container image |
| Docker Compose | - | Orchestration |

## External Integrations

| Service | Type | Purpose |
|---------|------|---------|
| CrowdSec LAPI | Required | Security decisions and alerts |
| Apprise API | Optional | Notification management |
| Auth0/Authentik | Optional | SSO authentication |

## Supported Notification Services (via Apprise)

- Email (SMTP)
- Telegram
- Discord
- Slack
- Gotify
- ntfy
- Pushover
- Matrix
- Webhooks
- And 70+ more services

## Security Features

- Random password generation on first run
- Password stored in `/app/.auth_password` (mode 0600)
- HTTP-only session cookies
- CORS with credentials support
- Auth0/Authentik SSO integration

## License

MIT License
