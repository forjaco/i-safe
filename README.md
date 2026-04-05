# I-safe

**I-safe** is an open-source, self-hosted, local-first digital hygiene platform focused on exposure awareness, privacy analysis, and secure remediation guidance.

It was designed to help users understand their digital exposure, inspect privacy risks in uploaded images, and interact with a security-first interface that favors safe defaults, anti-abuse controls, and transparent architecture.

## Core focus

- Email exposure lookup
- Phone lookup in controlled mock mode
- Image privacy analysis (EXIF / metadata risk)
- Risk scoring and remediation guidance
- Secure authentication with rotation and reuse detection
- Local-first and self-hosted operation

## Current status

### Real / implemented
- Authentication:
  - Login
  - Refresh
  - Logout
  - Authenticated user endpoint (`/api/v1/auth/me`)
- Refresh token rotation
- Refresh token revocation
- Refresh token reuse attack detection
- Email lookup
- Image upload and privacy analysis
- Risk score calculation
- Actionable recommendations
- Anonymous restricted response mode
- Abuse protection / rate limiting
- Frontend integrated with backend
- i18n support:
  - Portuguese (pt-BR)
  - English (en)
  - Spanish (es)

### Controlled mock
- Phone lookup  
  Currently available as a **controlled mock flow** or disabled, depending on configuration.  
  It should **not** be presented as a real intelligence provider in production.

### Roadmap / coming soon
- Public image sanitization endpoint
- Encrypted vault
- Domain monitoring
- Digital hygiene report generation

## Security posture

I-safe was built with security as a first-class concern.

### Security-related features
- Argon2 password hashing
- JWT access + refresh token model
- Refresh rotation
- Reuse attack detection
- HttpOnly refresh cookie
- Access token stored only in memory on the frontend
- Structured logging without PII
- Request correlation (`request_id`)
- Restricted responses to reduce abuse value
- Rate limiting on OSINT and authentication flows
- Input validation for email and phone
- Safe image validation for:
  - empty files
  - oversized files
  - truncated files
  - mimetype mismatch
  - metadata / EXIF / GPS detection

### Abuse-aware design
This project is positioned as a **self-check / digital hygiene** platform.

It is **not** intended to support profiling, doxing, or offensive enumeration of third-party targets.

Some risk remains inherent to exposure lookup systems, so production deployments should use:
- strong reverse proxy / gateway enforcement
- distributed rate limiting
- robust logging and monitoring
- explicit environment configuration

## Architecture

Backend follows a Clean Architecture-inspired structure:

- `app/core/` → configuration, security, abuse prevention, middleware, errors
- `app/application/` → use cases, entities, ports
- `app/infrastructure/` → repositories, database adapters, external integrations
- `app/presentation/` → FastAPI routes
- `frontend/` → React + Vite frontend

## Stack

### Backend
- Python
- FastAPI
- SQLAlchemy 2.0
- Alembic
- Argon2
- JWT
- AES-GCM
- Pillow

### Frontend
- React 18
- Vite
- Axios

## Local development

### 1. Backend environment
Create local env from example:

```bash
cp .env.example .env
