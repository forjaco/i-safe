# Refresh Token Design

## Objetivo

Preparar a base para revogação e rotação futura de refresh tokens sem implementar ainda um sistema completo de autenticação multiusuário.

## Desenho

- Entidade de aplicação: `RefreshTokenRecord`
- Porta de repositório: `RefreshTokenRepository`
- Serviço de aplicação: `RefreshTokenService`
- Adapter leve para testes e evolução local: `InMemoryRefreshTokenRepository`
- Modelo SQLAlchemy preparado para persistência futura: `RefreshTokenRecordModel`

## Campos armazenados

- `jti`
- `sub`
- `token_type`
- `issued_at`
- `expires_at`
- `revoked_at`
- `reason`

## Estratégia atual

- `create_refresh_token()` já emite `jti` e `iat`
- `validate_refresh_token()` continua compatível e aceita um ponto de extensão opcional para checagem de revogação
- a revogação completa fica desacoplada no serviço de aplicação
- `rotate_refresh_token()` revoga automaticamente o refresh anterior e emite um novo token
- tokens rotacionados passam a carregar `parent_jti` para rastrear a cadeia
- se um refresh já revogado for reutilizado, `detect_reuse_attack()` marca o token como comprometido e revoga os demais tokens ativos do mesmo `sub`

## Fluxo de rotação

1. Cliente apresenta um refresh token válido.
2. O serviço valida `type`, `sub`, `jti` e o estado de revogação.
3. O token atual é revogado com motivo `rotated`.
4. Um novo refresh token é emitido com `parent_jti` apontando para o token anterior.
5. O novo token é registrado no repositório.

## Transporte HTTP adotado

- `access_token`: retornado no corpo da resposta para uso como `Authorization: Bearer`
- `refresh_token`: transportado em cookie `HttpOnly` com `SameSite` configurável
- `POST /api/v1/auth/login`: autentica com senha, retorna `access_token` e grava o cookie de refresh
- `POST /api/v1/auth/refresh`: lê o cookie de refresh, aplica rotação segura e devolve novo `access_token`
- `POST /api/v1/auth/logout`: revoga o refresh token atual e remove o cookie

Essa escolha reduz a exposição do refresh token ao JavaScript do frontend web. O fallback por header `Authorization: Bearer` continua aceito no backend para testes e integrações controladas.

## Reuse attack mitigado

Se um token já revogado voltar a ser usado:

- o token reutilizado é marcado como comprometido
- a cadeia ativa associada ao mesmo `sub` é revogada
- o chamador deve tratar a sessão como suspeita e exigir nova autenticação

## Trade-off de persistência

### Desenvolvimento local

O adapter in-memory é suficiente para testes e para organizar o desenho sem depender do runtime async atual do SQLite.

### Produção

Para produção, o repositório deve ser persistido em banco transacional. PostgreSQL async é a opção mais consistente para:

- revogação confiável entre múltiplos processos
- rotação de refresh token
- detecção de reuse attack de forma consistente
- auditoria operacional

SQLite local pode continuar útil em cenários single-node/self-hosted, mas o runtime atual desta máquina ainda apresenta instabilidade com `sqlite+aiosqlite`.
