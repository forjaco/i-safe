# Migrations

## Objetivo

Manter o schema do I-safe versionado de forma consistente entre desenvolvimento local e produção, sem depender de `create_all()` implícito.

## Ferramenta

- Alembic
- metadata alvo: `app.infrastructure.database.models.Base.metadata`

## Estado atual

A revisão inicial cria:

- `users`
- `leak_records`
- `refresh_tokens`

Arquivo inicial:

- `alembic/versions/20260405_000001_initial_schema.py`

## URL usada nas migrations

O Alembic usa a mesma estratégia do storage de autenticação:

- em desenvolvimento local: deriva uma URL sync a partir de `DATABASE_URL`
- em produção: usa `AUTH_DATABASE_URL` se existir
- caso contrário, deriva uma URL sync a partir de `PRODUCTION_DATABASE_URL`

Exemplos:

- `sqlite+aiosqlite:///./aegis.db` -> `sqlite:///./aegis.db`
- `postgresql://user:pass@db/isafe` -> `postgresql+psycopg://user:pass@db/isafe`
- `postgresql+asyncpg://user:pass@db/isafe` -> `postgresql+psycopg://user:pass@db/isafe`

## Como aplicar localmente

```bash
export PYTHONPATH=$PYTHONPATH:.
venv/bin/alembic upgrade head
```

## Como gerar nova revisão

```bash
export PYTHONPATH=$PYTHONPATH:.
venv/bin/alembic revision --autogenerate -m "describe change"
```

Revise a migration gerada antes de aplicar.

## Como aplicar em produção

1. Configure `PRODUCTION_DATABASE_URL` e, se necessário, `AUTH_DATABASE_URL`.
2. Execute as migrations antes de subir o tráfego da aplicação.
3. Só depois inicie os workers e o servidor HTTP.

## Observação importante

O runtime `sqlite+aiosqlite` continua instável nesta máquina para a trilha async. Isso não afeta o Alembic porque as migrations usam driver sync.
