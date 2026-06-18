# CrowdSec Dashboard - Development Plan

## Completed Tasks

### Phase 1: Frontend Migration
- [x] Migrate from Svelte 5 + Vite to vanilla HTML/CSS/JS
- [x] Simplify deployment (no build step required)
- [x] Apple-style dark UI design

### Phase 2: Authentication System
- [x] Add credentials-based authentication (AUTH_USERNAME/AUTH_PASSWORD)
- [x] Add Auth0/Authentik integration (AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET)
- [x] Session management with HTTP-only cookies
- [x] Login page with Apple-style design
- [x] Auto-detect auth method from backend
- [x] Password change functionality
- [x] Disable password login when SSO is configured
- [x] Auth provider settings display in UI

### Phase 3: UI Enhancements
- [x] Add password change functionality in Settings
- [x] Add tooltips for decision fields (type, scenario, origin)
- [x] Update README with documentation
- [x] Add pie charts for data visualization
- [x] Add statistics row with key metrics
- [x] Add APPRISE_CONFIG_URL support for remote config fetching
- [x] Show Auth0/Authentik configuration in settings
- [x] Add automatic light/dark mode based on browser/system preference
- [x] Remove time filter (CrowdSec API doesn't provide created_at data)
- [x] Remove "When" column (CrowdSec API doesn't provide timestamp data)

## Upcoming Tasks

### Phase 4: Security & UX
- [ ] Add rate limiting for login attempts
- [ ] Add session timeout configuration
- [ ] Add 2FA support (optional)
- [ ] Add audit log for actions
- [ ] Add IP whitelist for admin access

### Phase 5: Features
- [ ] Add export functionality (CSV, JSON)
- [ ] Add decision history/timeline with pagination
- [ ] Add custom notification rules per scenario
- [ ] Add multi-language support
- [ ] Add dark/light theme toggle
- [ ] Add real-time updates via WebSocket
- [ ] Add dashboard customization (drag & drop)
- [ ] Add alert aggregation by IP/country
- [ ] Add geo-location map for attacks

### Phase 6: DevOps
- [ ] Add health check endpoint with detailed status
- [ ] Add Prometheus metrics exporter
- [ ] Add Docker healthcheck
- [ ] Add backup/restore functionality
- [ ] Add Kubernetes Helm chart
- [ ] Add CI/CD pipeline
- [ ] Add automated tests (unit, e2e)

### Phase 7: Performance
- [ ] Add caching for API responses
- [ ] Add pagination for all lists
- [ ] Add lazy loading for charts
- [ ] Optimize database queries (if using DB)
- [ ] Add CDN support for static assets

### Phase 8: Integration
- [ ] Add support for multiple CrowdSec instances
- [ ] Add support for external databases (PostgreSQL, MySQL)
- [ ] Add support for Redis session storage
- [ ] Add webhooks for external integrations
- [ ] Add Slack/Discord bot integration

## Architecture

```
├── main.py              # Flask backend with auth
├── static/
│   ├── index.html      # Main HTML with login overlay
│   ├── app.js          # Frontend logic with auth & charts
│   └── style.css       # Apple-style dark theme
├── Dockerfile          # Python slim image
├── docker-compose.yml  # Container orchestration
├── .env.example        # Environment template
└── README.md           # Documentation
```

## Authentication Flow

1. User loads page
2. Frontend calls `/api/auth/status` to check auth config
3. If auth enabled:
   - Show login overlay
   - Credentials: show username/password form
   - SSO: show "Continue with SSO" button
4. User authenticates
5. Backend sets HTTP-only cookie
6. Frontend loads main dashboard with charts

## Chart Data Flow

1. User selects time period (day/week/month/all) from filter buttons
2. Frontend calls `/api/statistics?period=X`
3. Backend filters decisions by `created_at` field
4. Returns aggregated data for charts:
   - Decisions by type (ban, captcha, etc.)
   - Decisions by origin (crowdsec, manual, lists)
   - Top scenarios triggered
   - Events timeline breakdown
5. Chart displays "No data for this period" if empty

## Decision Tooltips Content

| Field | Description |
|-------|-------------|
| Type | The action taken: Ban (blocked), Captcha (challenge), or other |
| Scenario | The CrowdSec scenario that triggered this decision |
| Origin | Where the decision came from: CrowdSec, manual, or third-party |
| Duration | How long the ban will remain active |
| When | When the decision was created |

## Environment Variables

| Variable | Description |
|----------|-------------|
| AUTH_USERNAME | Login username (credentials mode) |
| AUTH_PASSWORD | Login password (credentials mode) |
| AUTH0_DOMAIN | Auth0/Authentik domain (SSO mode) |
| AUTH0_CLIENT_ID | Auth0/Authentik client ID |
| AUTH0_CLIENT_SECRET | Auth0/Authentik client secret |
| APPRISE_URLS | Comma-separated notification URLs |
| APPRISE_API_URL | External Apprise API URL |
| APPRISE_CONFIG_URL | Remote URL to fetch Apprise config |
