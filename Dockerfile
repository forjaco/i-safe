# STAGE 1: Compilação e Build
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .

# Instala ferramentas base do SO necessárias para compilação estrita (Argon2, Criptografia C)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    pip install --user --no-cache-dir -r requirements.txt && \
    apt-get purge -y --auto-remove gcc && \
    rm -rf /var/lib/apt/lists/*

# STAGE 2: Runtime (Estágio Limpo Final)
FROM python:3.11-slim

# Variáveis para proteger contra injeção de ByteCodes em cache e travas de buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Adiciona as libs compiladas no stage 1 ao Path root global
ENV PATH=/home/appuser/.local/bin:$PATH

WORKDIR /app

# Segurança A05: Criação nativa de usuário NÃO priviliegiado "appuser"
# Se houver RCE (Exploração de Comando) via endpoint vulnerável, o atacante cairá em Shell sem permissão de root
RUN addgroup --system appgroup && adduser --system --group appuser && chown -R appuser:appgroup /app
USER appuser

# Copiar os pacotes gerados no builder
COPY --from=builder --chown=appuser:appgroup /root/.local /home/appuser/.local

# Copiar os arquivos do Servidor
COPY --chown=appuser:appgroup . .

# Porta padronizada (usaremos nginx para mapear a 80/443 de fora pra ela)
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
