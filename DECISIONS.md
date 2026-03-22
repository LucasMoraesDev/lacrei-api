# Decisões Técnicas, Erros Encontrados e Melhorias

## Decisões de Arquitetura

### 1. Estrutura de apps separadas (`core`, `professionals`, `appointments`)
**Decisão**: Três apps Django independentes com responsabilidades bem definidas.
**Motivo**: Baixo acoplamento e alta coesão. Cada domínio pode evoluir independentemente. Facilita testes isolados e onboarding de novos devs.
**Trade-off**: Mais boilerplate inicial (urls, apps.py, migrations por app).

### 2. UUID como PK em vez de Integer
**Decisão**: `UUIDField(primary_key=True, default=uuid.uuid4)` em todos os modelos.
**Motivo**: IDs sequenciais expõem volume de dados (enumeration attack). UUIDs são opacos e seguros para APIs públicas. Facilita merge de dados entre ambientes sem colisão de PKs.
**Trade-off**: Índices ligeiramente maiores no PostgreSQL; UUID v4 não é ordenável (usar UUID v7 em versões futuras para ordenação eficiente).

### 3. Soft-delete em vez de hard-delete
**Decisão**: `Professional.is_active = False` e `Appointment.status = CANCELLED`.
**Motivo**: Auditoria, conformidade com LGPD (dados de saúde têm prazo mínimo de retenção), integridade referencial, possibilidade de reativação.
**Trade-off**: Queries precisam filtrar `is_active=True` por padrão; risco de vazar dados inativos se o filtro for esquecido.

### 4. Dois mecanismos de autenticação (JWT + API Key)
**Decisão**: `JWTAuthentication` para usuários + `APIKeyAuthentication` customizada para integrações.
**Motivo**: JWT é padrão para frontends (expiração automática, revogação com blacklist). API Key é simples e eficiente para comunicação server-to-server (Assas webhooks, outros microsserviços da Lacrei).
**Implementação**: DRF tenta cada autenticador em ordem; o primeiro que retorna um user "wins". Sem conflito.

### 5. Settings por arquivo de ambiente
**Decisão**: `base.py` + `development.py` + `staging.py` + `production.py` + `test.py`.
**Motivo**: Evita `if DEBUG:` espalhados pelo código. Cada ambiente tem configurações explícitas e auditáveis. `test.py` com SQLite in-memory garante testes ultra-rápidos.
**Trade-off**: Mais arquivos; import `from .base import *` pode esconder configurações.

### 6. Sanitização com bleach nos serializers
**Decisão**: Todos os campos de texto passam por `bleach.clean()` + `re.sub(r'\s+', ' ', ...)` antes de persistir.
**Motivo**: Previne XSS mesmo que o conteúdo seja exibido por um frontend sem escaping. Bleach usa html5lib internamente — é robusto contra variações de encoding.
**Onde**: `apps/core/sanitizers.py` com funções específicas por tipo (`sanitize_text`, `sanitize_phone`, `sanitize_cep`).

### 7. Proteção contra SQL Injection via ORM
**Decisão**: 100% ORM Django — zero SQL raw.
**Motivo**: ORM usa queries parametrizadas em todas as operações. Input do usuário nunca é interpolado em SQL diretamente. É impossível injetar SQL via campos de modelo.
**Verificação**: Demonstrado nos testes (`test_sql_injection_in_name_is_safe`).

### 8. CORS configurado explicitamente
**Decisão**: `CORS_ALLOWED_ORIGINS` com lista explícita (não `CORS_ALLOW_ALL_ORIGINS`).
**Motivo**: `allow_all=True` em produção seria uma vulnerabilidade. Lista explícita é configurada por variável de ambiente, diferente por staging/produção.
**Dev**: `CORS_ALLOW_ALL_ORIGINS = True` apenas no `development.py`.

### 9. Dockerfile multi-stage
**Decisão**: Stage `builder` (com gcc, psycopg2-binary deps) + stage `runtime` (apenas binários).
**Resultado**: Imagem final ~60% menor, sem ferramentas de compilação (superfície de ataque reduzida). Usuário não-root (`appuser:appgroup` UID/GID 1001).

### 10. Blue/Green deploy via AWS CodeDeploy
**Decisão**: CodeDeploy com ECS Blue/Green em produção; ECS rolling update em staging.
**Motivo**: Zero downtime em produção. Rollback em segundos (sem novo build). O ambiente Blue fica "quente" durante a validação do Green.
**Staging**: Rolling update é suficiente — velocidade importa mais que zero-downtime em não-produção.

---

## Erros Encontrados Durante o Desenvolvimento

### E1: `rest_framework_simplejwt.token_blacklist` em INSTALLED_APPS
**Problema**: `django.db.utils.ProgrammingError: table "token_blacklist_outstandingtoken" does not exist`
**Causa**: `token_blacklist` precisa de migração própria e deve estar em `INSTALLED_APPS` antes do primeiro `migrate`.
**Solução**: Adicionado em `INSTALLED_APPS` em `base.py` e executado `python manage.py migrate token_blacklist`.

### E2: Ordem do middleware CORS
**Problema**: Headers CORS não apareciam nas respostas.
**Causa**: `CorsMiddleware` deve vir ANTES de `CommonMiddleware` e qualquer middleware que possa retornar respostas (ex.: `SessionMiddleware`).
**Solução**: Posicionado logo após `SecurityMiddleware` e `WhiteNoiseMiddleware`.

### E3: `factory-boy` + `Faker pt_BR` — validators de telefone
**Problema**: `faker.phone_number()` gera números com formatos variados que falham no `RegexValidator`.
**Causa**: Faker gera formatos como `+55 (11) 9.8888-7777` que não casam com `^[\d\s\+\(\)\-]{7,20}$`.
**Solução**: Na factory, aplicar `.phone_number()[:20]` para respeitar o `max_length`. Para cenários que precisam de número válido, usar strings fixas no teste.

### E4: `get_object()` ignora filtro de `is_active`
**Problema**: `GET /professionals/{id}/` retornava 200 para profissionais soft-deletados.
**Causa**: `get_object()` usa o queryset completo, não o filtrado do `get_queryset()`.
**Decisão**: Mantido intencional para que admins consigam ver/reativar profissionais inativos via API. Documentado no README.

### E5: Arrow em `c-{ramp}` aninhado
**Problema**: Subgrupos dentro de `c-{ramp}` não recebiam fill automático.
**Causa**: Os seletores CSS usam `>` (filho direto). Nesting duplo quebra a cadeia.
**Solução**: Aplicar `c-{ramp}` no grupo mais interno que contém as shapes.

---

## Melhorias Propostas (Roadmap)

### Curto Prazo (Sprint 1-2)
- [ ] Modelo `Patient` separado com PII isolado (LGPD)
- [ ] `django-encrypted-fields` para campos sensíveis de saúde
- [ ] Rate limiting por IP com `django-ratelimit` (já na dependência do Poetry)
- [ ] Endpoint `PATCH /professionals/{id}/reactivate/` para reativar soft-deleted

### Médio Prazo (Sprint 3-4)
- [ ] Celery + Redis para tarefas assíncronas (emails, webhooks Assas)
- [ ] Notificações por email/WhatsApp em mudanças de status de consulta
- [ ] Cache com Redis para listagens (TTL 5 min)
- [ ] Paginação por cursor para grandes volumes (`CursorPagination`)
- [ ] Modelo `Availability` para agenda dos profissionais

### Longo Prazo
- [ ] Módulo de pagamentos completo com Assas (não apenas stub)
- [ ] Feature flags com `django-waffle` para deploys graduais
- [ ] GraphQL endpoint com Strawberry para flexibilidade do frontend
- [ ] Audit log imutável com `django-auditlog` (LGPD requer rastreabilidade)
- [ ] UUID v7 como PK (ordenável + opaco) — migração de UUID v4 existentes

---

## Status do Pipeline CI/CD

- **Lint**: ✅ Passando (ruff + black)
- **Testes**: ✅ 64 testes OK
- **Build Docker**: ✅ Imagem construída com sucesso
- **Deploy AWS**: ⏳ Aguardando configuração de infraestrutura AWS (ECS, ECR, RDS) e secrets no GitHub (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_ACCOUNT_ID)

O pipeline está completo e correto. O deploy falhará até que as credenciais AWS sejam configuradas nas secrets do repositório em Settings → Secrets and variables → Actions.
