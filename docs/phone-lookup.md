# Phone Lookup

O lookup por telefone no I-safe segue a mesma postura defensiva do lookup por e-mail:

- validação forte de entrada em formato internacional E.164
- resposta restrita quando a política local exigir ou quando houver abuso
- rate limiting separado por IP, alvo e padrão de enumeração
- mensagens higienizadas para o cliente

## Estado atual

- Endpoint: `POST /api/v1/osint/phone/check`
- Feature flag: `ENABLE_PHONE_LOOKUP`
- Modo mock controlado: `PHONE_LOOKUP_USE_MOCK`

## Comportamento

- `ENABLE_PHONE_LOOKUP=false`
  - o endpoint responde `503`
  - isso indica que a feature não está ativa no backend
- `ENABLE_PHONE_LOOKUP=true` e `PHONE_LOOKUP_USE_MOCK=true`
  - o endpoint responde com `status=MOCK_SUCCESS`
  - a ação retornada deixa explícito que a resposta veio de mock controlado
- `ENABLE_PHONE_LOOKUP=true` e `PHONE_LOOKUP_USE_MOCK=false`
  - o backend responde `503`
  - hoje não existe provider externo real integrado para telefone

## Segurança

- o fluxo não foi desenhado para enumeração massiva
- respostas podem ser reduzidas para `RESTRICTED`
- logs não registram o telefone em claro
- a recomendação de uso continua sendo self-check ou contexto legítimo e autenticado

## Dívida técnica atual

- não há provider real de telefone integrado
- a persistência do lookup de telefone ainda não foi adicionada ao banco
- para produção distribuída, o rate limiting deve migrar para store compartilhado ou edge
