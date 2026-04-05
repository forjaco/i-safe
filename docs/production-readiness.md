# Production Readiness

## Banco

- desenvolvimento local-first: SQLite
- produção oficial: PostgreSQL
- camada async principal: `postgresql+asyncpg`
- storage persistente de autenticação/migrations: `postgresql+psycopg`

## Autenticação

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- refresh token em cookie `HttpOnly`
- access token via `Bearer`
- fallback de refresh token via header deve permanecer desabilitado em produção
- endpoints de auth possuem rate limit separado do módulo OSINT

## Operação

- `GET /health` para liveness
- `GET /ready` para readiness
- `TrustedHostMiddleware` ativo
- limite global de request por `HTTP_MAX_REQUEST_SIZE_BYTES`
- logs com `request_id`
- store de rate limit atual é in-memory e serve para dev/single-node
- para produção com múltiplos processos/nós, o mesmo contrato deve ser ligado a store compartilhado/gateway externo

## Configuração mínima para produção

- `ENVIRONMENT=production`
- `SECRET_KEY` forte
- `ENCRYPTION_KEY` válida
- `ALLOWED_ORIGINS` explícito
- `ALLOWED_HOSTS` explícito
- `PRODUCTION_DATABASE_URL` apontando para PostgreSQL
- `AUTH_COOKIE_SECURE=true`
- `HIBP_API_KEY` real ou `EMAIL_CHECK_USE_MOCK=true` para ambientes controlados
- `ENABLE_REFRESH_HEADER_FALLBACK=false`

## Itens que não devem ser tratados como produção

- credenciais de demo local, como `demo@isafe.local`, existem apenas para desenvolvimento e demonstração controlada
- `PHONE_LOOKUP_USE_MOCK=true` significa resposta mock controlada, não provider real
- defaults de exemplo como `change-me-in-production` no `docker-compose.yml` não são senhas aceitáveis para ambientes públicos

## Limitações conhecidas

- `sqlite+aiosqlite` segue instável neste runtime atual e continua `xfail` nos testes de infraestrutura
- a rota de OSINT pode operar em modo diagnóstico local com `OSINT_PERSIST_RESULTS=false`
