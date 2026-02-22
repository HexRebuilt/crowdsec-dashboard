# CrowdSec Dashboard - Development Plan

## Completed Tasks

### Phase 1: Frontend Migration
- [x] Migrate from Svelte 5 + Vite to vanilla HTML/CSS/JS
- [x] Simplify deployment (no build step required)
- [x] Apple-style dark UI design

### Phase 2: Authentication System
- [x] Add credentials-based authentication (AUTH_USERNAME/AUTH_PASSWORD)
- [x] Add Auth0 integration (AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET)
- [x] Session management with HTTP-only cookies
- [x] Login page with Apple-style design
- [x] Auto-detect auth method from backend

### Phase 3: UI Enhancements
- [x] Add password change functionality in Settings
- [x] Add tooltips for decision fields (type, scenario, origin)
- [x] Disable password login when Auth0 is configured
- [x] Update README with documentation

## Upcoming Tasks

### Phase 4: Security & UX
- [ ] Add rate limiting for login attempts
- [ ] Add session timeout configuration
- [ ] Add 2FA support (optional)

### Phase 5: Features
- [ ] Add export functionality (CSV, JSON)
- [ ] Add decision history/timeline
- [ ] Add custom notification rules
- [ ] Add multi-language support

### Phase 6: DevOps
- [ ] Add health check endpoint
- [ ] Add Prometheus metrics
- [ ] Add Docker healthcheck
- [ ] Add backup/restore functionality

## Architecture

```
├── app.py              # Flask backend with auth
├── static/
│   ├── index.html      # Main HTML with login overlay
│   ├── app.js          # Frontend logic with auth
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
   - Auth0: show "Continue with Auth0" button
4. User authenticates
5. Backend sets HTTP-only cookie
6. Frontend loads main dashboard

## Decision Tooltips Content

| Field | Description |
|-------|-------------|
| Type | The action taken: Ban (blocked), Captcha (challenge), or other |
| Scenario | The CrowdSec scenario that triggered this decision |
| Origin | Where the decision came from: CrowdSec, manual, or third-party |
| Duration | How long the ban will remain active |
