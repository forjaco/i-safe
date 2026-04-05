cat << 'EOF' > README.md
# I-safe

I-safe is an open-source, self-hosted digital hygiene platform focused on exposure awareness, privacy analysis, and security-first design.

## Features

- Email exposure lookup
- Phone lookup (controlled mock mode)
- Image privacy analysis (EXIF / metadata)
- Risk scoring and recommendations
- Secure authentication with refresh token rotation
- Abuse protection and rate limiting
- i18n support (pt-BR, en, es)

## Current Status

### Implemented
- Authentication (login, refresh, logout, /auth/me)
- Email lookup
- Image upload and analysis
- Risk score and recommendations
- Anti-abuse protections

### Mock / Controlled
- Phone lookup (not a real provider yet)

### Roadmap
- Image sanitization
- Vault
- Domain monitoring
- Hygiene report export

## Security

- Argon2 password hashing
- JWT access + refresh tokens
- Refresh rotation and reuse detection
- HttpOnly cookies
- No PII in logs
- Input validation and safe image handling

## Architecture

- Clean Architecture
- FastAPI backend
- React + Vite frontend

## Setup

### Backend

cp .env.example .env

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
pip install -r requirements-dev.txt

venv/bin/python scripts/seed_demo_user.py

venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001

### Frontend

cp frontend/.env.example frontend/.env

cd frontend
npm install
npm run dev

Frontend:
http://localhost:5173

## Demo Credentials

Email: demo@isafe.local  
Password: DemoPass123!

(Local development only)

## Tests

venv/bin/pytest -q

## Limitations

- Phone lookup is mock
- SQLite async has runtime limitations
- Rate limit is in-memory (dev oriented)

## Production Notes

- Use PostgreSQL
- Use real secrets outside repo
- Enable secure cookies
- Use gateway rate limiting

## License

MIT License

## Disclaimer

I-safe is intended for defensive, privacy-oriented, and self-assessment use cases.

Do not use it to:
- profile individuals
- target third parties
- violate privacy or legal boundaries

EOF
