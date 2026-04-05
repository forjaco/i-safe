# Development Stack

## Objetivo atual

O I-safe é local-first. O backend mantém compatibilidade com SQLAlchemy 2.0 async e usa SQLite como padrão de desenvolvimento.

## Stack suportada hoje

- Python 3.12
- FastAPI
- SQLAlchemy 2.0 async
- SQLite via `sqlite+aiosqlite` como padrão local

## Banco de dados

### Desenvolvimento local

- `DATABASE_URL=sqlite+aiosqlite:///./aegis.db`
- simples para uso self-hosted local
- suficiente para desenvolvimento e testes de integração quando o runtime suporta `aiosqlite`

### Produção self-hosted

PostgreSQL async é a recomendação arquitetural para produção:

- melhor concorrência
- melhor observabilidade operacional
- menos dependência de peculiaridades do runtime local com SQLite async
- melhor persistência para revogação/rotação de refresh token e detecção de reuse

O código já aceita um `DATABASE_URL` async compatível sem exigir reescrita da aplicação.
Para produção, prefira definir `PRODUCTION_DATABASE_URL=postgresql://...`; a aplicação promove a URL para `postgresql+asyncpg` na camada async e para `postgresql+psycopg` no storage/migrations sync.

## Limitação conhecida

No runtime atual desta máquina, `sqlite+aiosqlite` falha antes do app, em `await aiosqlite.connect(...)`.

Por isso:

- os testes de infraestrutura async estão marcados como `xfail`
- a limitação não deve ser mascarada
- use `scripts/runtime_async_probe.py` para revalidação do ambiente

## Hardening operacional

- `ALLOWED_HOSTS` deve ser explícito em produção; wildcard não é aceito.
- `HTTP_MAX_REQUEST_SIZE_BYTES` limita payloads no edge da aplicação.
- `IMAGE_MAX_FILE_SIZE_BYTES` e `IMAGE_MAX_PIXELS` limitam uploads de imagem e reduzem risco de decompression bomb.
- `HIBP_TIMEOUT_SECONDS`, `HIBP_MAX_RETRIES` e `HIBP_RETRY_BACKOFF_SECONDS` controlam resiliência da integração externa.
- `/health` indica vida do processo; `/ready` valida o storage de autenticação.
- use `docs/migrations.md` para versionar o schema com Alembic.
