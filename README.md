# 🏥 Lacrei Saúde — API de Gerenciamento de Consultas Médicas

[![CI/CD Pipeline](https://github.com/lacreisaude/lacrei-api/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/lacreisaude/lacrei-api/actions)
[![Coverage](https://codecov.io/gh/lacreisaude/lacrei-api/badge.svg)](https://codecov.io/gh/lacreisaude/lacrei-api)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.0-green.svg)](https://djangoproject.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> API RESTful segura e pronta para produção para gerenciamento de profissionais de saúde e consultas médicas, desenvolvida para a **Lacrei Saúde** — plataforma de saúde inclusiva LGBTQIA+.

---

## 📋 Sumário

- [Tecnologias](#-tecnologias)
- [Arquitetura](#-arquitetura)
- [Setup Local](#-setup-local)
- [Setup com Docker](#-setup-com-docker)
- [Variáveis de Ambiente](#-variáveis-de-ambiente)
- [Executando os Testes](#-executando-os-testes)
- [Documentação da API](#-documentação-da-api)
- [CI/CD e Deploy](#-cicd-e-deploy)
- [Rollback](#-rollback)
- [Integração com Assas](#-integração-com-assas)
- [Decisões Técnicas](#-decisões-técnicas)
- [Melhorias Propostas](#-melhorias-propostas)

---

## 🛠 Tecnologias

| Camada           | Tecnologia                             |
|------------------|----------------------------------------|
| Linguagem        | Python 3.11                            |
| Framework        | Django 5.0 + Django REST Framework 3.15|
| Banco de dados   | PostgreSQL 16                          |
| Autenticação     | JWT (SimpleJWT) + API Key              |
| Containerização  | Docker + Docker Compose                |
| CI/CD            | GitHub Actions                         |
| Deploy           | AWS ECS (Fargate) + ECR + CodeDeploy  |
| Monitoramento    | Sentry + CloudWatch Logs               |
| Docs da API      | drf-spectacular (Swagger + Redoc)      |
| Gerenciador deps | Poetry 1.8                             |
| Testes           | pytest + APITestCase + factory-boy     |
| Lint             | Ruff + Black + Mypy                    |

---

## 🏗 Arquitetura

```
lacrei-api/
├── apps/
│   ├── core/               # Middleware, auth, sanitização, exceções, logs
│   ├── professionals/      # CRUD de Profissionais de Saúde
│   └── appointments/       # CRUD de Consultas Médicas
├── config/
│   ├── settings/
│   │   ├── base.py         # Configurações compartilhadas
│   │   ├── development.py  # Dev local
│   │   ├── staging.py      # Ambiente de staging (AWS)
│   │   ├── production.py   # Produção (AWS) com SSL obrigatório
│   │   └── test.py         # SQLite in-memory para testes rápidos
│   └── urls.py
├── tests/
│   ├── factories.py        # Factory Boy (geração de dados de teste)
│   ├── test_professionals.py
│   ├── test_appointments.py
│   └── test_health_security.py
├── docs/
│   └── assas_integration.py  # Proposta de integração com Assas
├── docker/
│   ├── entrypoint.sh
│   └── postgres/init.sql
├── .github/workflows/
│   ├── ci-cd.yml           # Pipeline completo (lint → test → build → deploy)
│   ├── pr-checks.yml       # Validação rápida em Pull Requests
│   └── rollback.yml        # Rollback manual via workflow_dispatch
├── Dockerfile              # Multi-stage build (builder + runtime)
├── docker-compose.yml      # Ambiente local com PostgreSQL
├── pyproject.toml          # Poetry + configuração de ferramentas
└── manage.py
```

### Endpoints Principais

| Método   | Endpoint                                  | Descrição                                    |
|----------|-------------------------------------------|----------------------------------------------|
| `GET`    | `/api/v1/professionals/`                  | Listar profissionais (com filtros e busca)   |
| `POST`   | `/api/v1/professionals/`                  | Cadastrar profissional                       |
| `GET`    | `/api/v1/professionals/{id}/`             | Detalhar profissional                        |
| `PATCH`  | `/api/v1/professionals/{id}/`             | Atualizar parcialmente                       |
| `PUT`    | `/api/v1/professionals/{id}/`             | Atualizar completamente                      |
| `DELETE` | `/api/v1/professionals/{id}/`             | Soft-delete (marca como inativo)             |
| `GET`    | `/api/v1/professionals/{id}/appointments/`| **Buscar consultas por profissional**        |
| `GET`    | `/api/v1/appointments/`                   | Listar consultas (filtro por ?professional=) |
| `POST`   | `/api/v1/appointments/`                   | Agendar consulta                             |
| `GET`    | `/api/v1/appointments/{id}/`              | Detalhar consulta                            |
| `PATCH`  | `/api/v1/appointments/{id}/`              | Atualizar consulta                           |
| `DELETE` | `/api/v1/appointments/{id}/`              | Cancelar consulta (soft-cancel)              |
| `PATCH`  | `/api/v1/appointments/{id}/cancel/`       | Cancelar com motivo obrigatório              |
| `POST`   | `/api/v1/auth/token/`                     | Obter JWT (login)                            |
| `POST`   | `/api/v1/auth/token/refresh/`             | Renovar JWT                                  |
| `GET`    | `/api/v1/health/`                         | Health check (sem autenticação)              |
| `GET`    | `/api/docs/`                              | Swagger UI                                   |
| `GET`    | `/api/redoc/`                             | Redoc                                        |

---

## 💻 Setup Local

### Pré-requisitos

- Python 3.11+
- Poetry 1.8+
- PostgreSQL 16+

### 1. Clonar o repositório

```bash
git clone https://github.com/lacreisaude/lacrei-api.git
cd lacrei-api
```

### 2. Instalar dependências

```bash
poetry install
```

### 3. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Edite o .env com suas configurações locais
```

### 4. Criar o banco de dados

```bash
# No PostgreSQL:
createdb lacrei_db
createuser lacrei_user
psql -c "ALTER USER lacrei_user WITH PASSWORD 'lacrei_pass';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE lacrei_db TO lacrei_user;"
```

### 5. Executar migrações e criar superusuário

```bash
poetry run python manage.py migrate --settings=config.settings.development
poetry run python manage.py createsuperuser --settings=config.settings.development
```

### 6. Iniciar o servidor

```bash
poetry run python manage.py runserver --settings=config.settings.development
```

API disponível em: http://localhost:8000  
Swagger UI: http://localhost:8000/api/docs/  
Admin Django: http://localhost:8000/admin/

---

## 🐳 Setup com Docker

### Pré-requisitos

- Docker 24+
- Docker Compose v2+

### 1. Subir os serviços

```bash
# Clonar e entrar no projeto
git clone https://github.com/lacreisaude/lacrei-api.git
cd lacrei-api

# Copiar variáveis de ambiente
cp .env.example .env

# Subir API + PostgreSQL
docker compose up -d

# Verificar logs
docker compose logs -f api
```

### 2. Verificar health check

```bash
curl http://localhost:8000/api/v1/health/
# Resposta: {"status": "healthy", "database": "ok", ...}
```

### 3. Acessar com API Key (desenvolvimento)

```bash
curl -H "X-API-Key: dev-api-key-change-in-prod" \
     http://localhost:8000/api/v1/professionals/
```

### 4. Subir com pgAdmin (opcional)

```bash
docker compose --profile tools up -d
# pgAdmin disponível em: http://localhost:5050
# Login: admin@lacrei.local / admin123
```

### 5. Parar os serviços

```bash
docker compose down        # Para os containers
docker compose down -v     # Para e remove volumes (apaga dados!)
```

---

## 🔐 Variáveis de Ambiente

| Variável                | Obrigatória em prod | Descrição                                    |
|-------------------------|---------------------|----------------------------------------------|
| `SECRET_KEY`            | ✅                  | Chave secreta Django (nunca commite!)        |
| `DEBUG`                 | ✅ (`False`)        | Desabilitar em produção                      |
| `DJANGO_SETTINGS_MODULE`| ✅                  | `config.settings.production`                 |
| `DB_NAME`               | ✅                  | Nome do banco de dados                       |
| `DB_USER`               | ✅                  | Usuário do PostgreSQL                        |
| `DB_PASSWORD`           | ✅                  | Senha do PostgreSQL                          |
| `DB_HOST`               | ✅                  | Host do PostgreSQL (RDS em produção)         |
| `ALLOWED_HOSTS`         | ✅                  | Hosts permitidos (vírgula-separados)         |
| `CORS_ALLOWED_ORIGINS`  | ✅                  | Origens CORS permitidas                      |
| `VALID_API_KEYS`        | ✅                  | API Keys válidas (vírgula-separadas)         |
| `SENTRY_DSN`            | Recomendado         | DSN do Sentry para monitoramento de erros    |

---

## 🧪 Executando os Testes

### Com Poetry (local)

```bash
# Todos os testes com cobertura
poetry run pytest -v

# Apenas testes de profissionais
poetry run pytest tests/test_professionals.py -v

# Apenas testes de consultas
poetry run pytest tests/test_appointments.py -v

# Com relatório de cobertura HTML
poetry run pytest --cov=apps --cov-report=html
open htmlcov/index.html

# Cobertura mínima de 80% (falha se abaixo)
poetry run pytest --cov=apps --cov-fail-under=80
```

### Com Django test runner (APITestCase)

```bash
# Todos os testes
poetry run python manage.py test tests --settings=config.settings.test -v 2

# Módulo específico
poetry run python manage.py test tests.test_professionals --settings=config.settings.test

# Teste específico
poetry run python manage.py test tests.test_appointments.AppointmentByProfessionalTest \
  --settings=config.settings.test
```

### Com Docker

```bash
docker compose -f docker-compose.ci.yml up --abort-on-container-exit
```

### Cobertura dos testes

| Módulo                    | Cenários cobertos                                                |
|---------------------------|------------------------------------------------------------------|
| `test_professionals.py`   | Auth, CRUD completo, soft-delete, XSS, SQL injection, filtros   |
| `test_appointments.py`    | Auth, CRUD completo, cancelamento, filtro por profissional, erros|
| `test_health_security.py` | Health check, CORS, headers de segurança, sanitização           |

---

## 📚 Documentação da API

Com o servidor rodando:

- **Swagger UI**: http://localhost:8000/api/docs/
- **Redoc**: http://localhost:8000/api/redoc/
- **OpenAPI JSON**: http://localhost:8000/api/schema/

### Autenticação na documentação

**Via JWT:**
1. `POST /api/v1/auth/token/` com `{"username": "user", "password": "pass"}`
2. Copie o `access` token
3. Authorize no Swagger com `Bearer <token>`

**Via API Key:**
1. Adicione o header `X-API-Key: <sua-api-key>`

---

## 🚀 CI/CD e Deploy

### Pipeline GitHub Actions

```
Push/PR → Lint → Testes → Build Docker → Deploy
```

| Branch    | Trigger       | Action                                    |
|-----------|---------------|-------------------------------------------|
| Qualquer  | Pull Request  | Lint + Testes rápidos + check migrações   |
| `staging` | Push          | Lint → Testes → Build → Deploy Staging    |
| `main`    | Push          | Lint → Testes → Build → Deploy Produção (Blue/Green) |

### Infraestrutura AWS

```
GitHub Actions
    ↓ push image
Amazon ECR (Elastic Container Registry)
    ↓ deploy
Amazon ECS (Fargate) — sem gerenciamento de servidores
    ↓ balanceamento
Application Load Balancer (ALB)
    ↓ banco de dados
Amazon RDS PostgreSQL (Multi-AZ em produção)
    ↓ logs
Amazon CloudWatch Logs
```

### Deploy manual (emergência)

```bash
# Atualizar apenas a imagem no ECS
aws ecs update-service \
  --cluster lacrei-production \
  --service lacrei-api-production \
  --force-new-deployment \
  --region us-east-1
```

---

## 🔄 Rollback

### Rollback automático (falha no deploy)

O workflow de CI/CD detecta falha no health check e reverte automaticamente para a task definition anterior:

```yaml
# Trecho do ci-cd.yml
- name: Rollback automático em caso de falha
  if: failure()
  run: |
    aws ecs update-service \
      --task-definition lacrei-api-production:$((CURRENT - 1)) \
      --force-new-deployment
```

### Rollback manual (via GitHub Actions)

1. Acesse **Actions → 🔄 Rollback Manual**
2. Clique em **Run workflow**
3. Selecione o ambiente (`staging` ou `production`)
4. Informe a revisão alvo (ou deixe vazio para a anterior)
5. Informe o motivo
6. Clique em **Run**

```bash
# Equivalente via CLI
aws ecs update-service \
  --cluster lacrei-production \
  --service lacrei-api-production \
  --task-definition lacrei-api-production:42 \  # revisão estável
  --force-new-deployment
```

### Rollback via Git (código)

```bash
# Revert de um commit específico
git revert <commit-sha> --no-edit
git push origin main
# O pipeline é acionado automaticamente
```

### Estratégia Blue/Green (produção)

O deploy em produção usa **AWS CodeDeploy com Blue/Green**:

1. **Blue** = ambiente atual (em produção)
2. **Green** = nova versão (sendo validada)
3. O ALB redireciona tráfego gradualmente para o Green
4. Se o health check falhar → tráfego volta ao Blue automaticamente
5. Janela de rollback configurável (ex.: 10 minutos)

---

## 💳 Integração com Assas

Veja a proposta completa em [`docs/assas_integration.py`](docs/assas_integration.py).

### Fluxo resumido

```
1. Paciente agenda consulta → Appointment{status: SCHEDULED}
       ↓
2. Sistema chama Assas → cria cobrança (Pix/Boleto/Cartão)
       ↓
3. Assas retorna payment_id + link de pagamento
       ↓
4. Paciente paga → Assas envia webhook
       ↓
5. /api/v1/payments/webhook/ → Appointment{payment_status: CONFIRMED}
       ↓
6. Split automático: Lacrei retém taxa, repassa ao profissional
```

### Split de pagamento

O Assas suporta split nativo via campo `split` no payload:

```json
{
  "customer": "cus_xxx",
  "value": 200.00,
  "split": [{
    "walletId": "wallet_do_profissional",
    "percentualValue": 80
  }]
}
```

Lacrei retém 20%, profissional recebe 80% automaticamente.

---

## 🧠 Decisões Técnicas

### 1. Django ORM em vez de SQL raw → Proteção contra SQL Injection
O Django ORM usa **queries parametrizadas** em 100% das operações. Nunca há interpolação direta de input do usuário em SQL. Isso é mais seguro e mais legível que SQL raw.

### 2. Soft-delete em vez de hard-delete
Profissionais e consultas nunca são deletados fisicamente. Isso:
- Preserva o histórico de consultas
- Permite auditoria
- Evita erros de integridade referencial
- Facilita recuperação de dados

### 3. Dois mecanismos de autenticação (JWT + API Key)
- **JWT**: para usuários humanos (frontend, admin)
- **API Key**: para integrações service-to-service (Assas, outros microsserviços da Lacrei)
Ambos coexistem sem conflito graças à ordem em `DEFAULT_AUTHENTICATION_CLASSES`.

### 4. Settings por ambiente
Cada ambiente tem seu próprio arquivo de settings, evitando condicionais `if DEBUG:` espalhados pelo código. O settings de teste usa **SQLite in-memory** para testes ultra-rápidos sem necessidade de PostgreSQL no CI básico.

### 5. Multi-stage Dockerfile
O stage `builder` instala compiladores e dependências de build. O stage `runtime` copia apenas os binários compilados — a imagem final é **~60% menor** e sem ferramentas de build (superfície de ataque reduzida).

### 6. Sanitização com bleach
Todos os campos de texto são sanitizados com `bleach.clean()` no serializer antes de persistir. Isso previne XSS mesmo que o conteúdo seja exibido em um frontend sem escaping adequado.

### 7. Poetry para gerenciamento de dependências
O `poetry.lock` garante builds **100% reproduzíveis** em qualquer ambiente. O `pyproject.toml` unifica configuração de deps, lint, testes e build em um único arquivo.

### 8. Factory Boy para testes
Factories geram dados realistas em português (com `Faker("pt_BR")`), tornando os testes mais próximos da realidade e fáceis de manter.

### 9. Deploy Blue/Green em produção
Elimina downtime durante deploys. Em caso de falha, o rollback é instantâneo (segundos) pois o ambiente Blue continua rodando durante a validação do Green.

---

## 🚧 Melhorias Propostas

| Prioridade | Melhoria                                                        | Justificativa                                      |
|------------|------------------------------------------------------------------|----------------------------------------------------|
| Alta       | Modelo de Paciente separado (com PII isolado)                   | LGPD — dados sensíveis de saúde exigem controle   |
| Alta       | Criptografia de campos sensíveis (django-encrypted-fields)       | LGPD — dados de saúde são sensíveis                |
| Alta       | Rate limiting por IP e por usuário (django-ratelimit)            | Prevenção de abuso e brute-force                   |
| Média      | Notificações (email/WhatsApp) em mudanças de status de consulta  | UX e confirmação de agendamentos                   |
| Média      | Cache com Redis (django-redis) para listagens                    | Performance em produção                            |
| Média      | Async tasks com Celery (envio de emails, webhooks Assas)         | Não bloquear a requisição HTTP                     |
| Média      | Paginação por cursor para grandes volumes                        | Performance em tabelas com milhões de registros    |
| Baixa      | GraphQL endpoint (Strawberry)                                    | Flexibilidade para o frontend                      |
| Baixa      | Feature flags (django-waffle)                                    | Deploy gradual de funcionalidades                  |

---

## 📄 Erros encontrados e lições aprendidas

Documentados durante o desenvolvimento:

1. **`rest_framework_simplejwt.token_blacklist` requer migração própria** — precisa estar em `INSTALLED_APPS` antes de rodar `migrate`.
2. **CORS + `CorsMiddleware` deve vir antes de `CommonMiddleware`** — ordem importa no middleware stack do Django.
3. **`APITestCase` não usa banco in-memory por padrão** — o `test.py` settings deve apontar explicitamente para SQLite `:memory:` ou PostgreSQL de teste.
4. **`factory-boy` com `faker pt_BR`** — números de telefone e CEPs gerados podem não passar em validators rígidos; ajustar factories conforme necessário.
5. **Soft-delete + `is_active` filter** — o queryset padrão do viewset filtra `is_active=True`, mas o `get_object()` busca em todos (incluindo inativos). Isso é intencional para que admins possam reativar profissionais.

---

## 📝 Licença

MIT © Lacrei Saúde — Plataforma de saúde inclusiva LGBTQIA+
