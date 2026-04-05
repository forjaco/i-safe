# Runtime Notes

## SQLite async no ambiente atual

O projeto usa `sqlite+aiosqlite` como backend local-first padrão.

No ambiente atual de execução foi reproduzida uma falha específica em `await aiosqlite.connect(...)`.
O problema ocorre:

- em script mínimo fora do `pytest`
- em testes com `pytest-asyncio`
- na engine async do SQLAlchemy 2.0

O comportamento indica um problema de runtime/infraestrutura do ambiente atual, não do contrato HTTP da aplicação.

Enquanto esse ambiente continuar instável:

- mantenha os testes de infraestrutura async explicitamente marcados como `xfail`
- não substitua silenciosamente por acesso síncrono na aplicação
- use o probe em `scripts/runtime_async_probe.py` para revalidação
- se precisar manter `POST /api/v1/osint/check` funcional localmente, use `OSINT_PERSIST_RESULTS=false` apenas em modo diagnóstico
- para revogação/rotação persistente de refresh token em produção, prefira PostgreSQL async
- migrations Alembic usam driver sync e não dependem da trilha `sqlite+aiosqlite`

## Hardening operacional

- `TrustedHostMiddleware` depende de `ALLOWED_HOSTS` correto no ambiente.
- payloads são limitados no edge por `HTTP_MAX_REQUEST_SIZE_BYTES`.
- o upload de imagem aplica limites de tamanho e resolução e continua processando apenas em memória.
- `/health` serve para liveness; `/ready` verifica a prontidão do storage de autenticação.
