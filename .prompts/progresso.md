# 📋 Willu — Registro de Progresso

> Última atualização: 2026-03-07 (projeção variáveis com média + natureza Esporádica)
> Propósito: Servir de contexto para LLMs nas próximas iterações de desenvolvimento.

---

## 1. Visão Geral do Projeto

App web de **finanças pessoais** focado em **projeção de saldo futuro** e **conciliação inteligente de extratos bancários**. Single-player. O PRD completo está em `prompt-prd.md`.

**Stack:** Python 3.11 · FastAPI · SQLAlchemy async · PostgreSQL · Jinja2 · HTMX · Tailwind CSS (CDN) · Chart.js · pytest

---

## 2. Estrutura de Arquivos Atual

```
willu/
├── app/
│   ├── __init__.py
│   ├── main.py                  # Entrypoint FastAPI, lifespan cria tabelas
│   ├── config.py                # Settings via pydantic-settings + .env
│   ├── database.py              # Engine async + sessionmaker + Base + get_db
│   │
│   ├── models/
│   │   ├── __init__.py          # Re-exporta todos os models
│   │   ├── conta.py             # Conta (id, nome, saldo_inicial)
│   │   ├── categoria.py         # Categoria (id, nome, tipo, natureza) + enums
│   │   ├── transacao.py         # Transacao (ciclo Projetada→Executada) + property valor_efetivo
│   │   └── dicionario_conciliacao.py  # DicionarioConciliacao (aprendizado)
│   │
│   ├── schemas/
│   │   ├── __init__.py          # Re-exporta todos os schemas
│   │   ├── conta.py             # ContaCreate, ContaUpdate, ContaRead
│   │   ├── categoria.py         # CategoriaCreate, CategoriaUpdate, CategoriaRead
│   │   ├── transacao.py         # TransacaoCreate, TransacaoUpdate, TransacaoRead
│   │   └── conciliacao.py       # LinhaExtrato, SugestaoConciliacao, ConfirmacaoConciliacao
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── projecao.py          # calcular_projecao (async) + calcular_projecao_sync
│   │   ├── conciliacao.py       # Motor 3 camadas (async + sync). confirmar_conciliacao
│   │   └── importacao.py        # importar_ofx, importar_csv, detectar_formato
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── dashboard.py         # GET / (dashboard), /api/projecao, /api/calendario
│   │   ├── contas.py            # CRUD /contas/ (GET, POST, PUT, DELETE)
│   │   ├── categorias.py        # CRUD /categorias/ + /categorias/options
│   │   ├── transacoes.py        # CRUD /transacoes/ + /form + /form/{id} (modal)
│   │   └── importacao.py        # /importacao/ + /upload + /confirmar + /confirmar-todas
│   │
│   └── templates/
│       ├── base.html            # Layout master: navbar, FAB, modal genérico, CDNs
│       ├── dashboard.html       # Cards resumo + gráfico Chart.js + calendário HTMX
│       ├── transacoes.html      # Filtros + lista com auto-refresh HTMX
│       ├── categorias.html      # Form inline + tabela
│       ├── contas.html          # Form inline + grid cards
│       ├── importacao.html      # Upload + box explicativo
│       └── partials/
│           ├── grafico.html           # Chart.js partial (HTMX swap)
│           ├── calendario.html        # Grid 7 colunas, navegação mês, cores por saldo
│           ├── transacoes_lista.html  # Tabela com badges, ações editar/excluir
│           ├── transacao_form.html    # Modal form: tipo, valor, data, conta, categoria, status
│           ├── categorias_lista.html  # Tabela com badges tipo/natureza
│           ├── contas_lista.html      # Grid cards com nome e saldo
│           └── conciliacao_lista.html # Tabela de sugestões + confirmar individual/todas
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Fixtures: SQLite in-memory, AsyncClient, db_session
│   ├── test_api.py              # 40 testes — integração HTTP (contas, categorias, transações, dashboard, importação)
│   ├── test_schemas.py          # 22 testes — validação Pydantic schemas
│   ├── test_models.py           # 17 testes — valor_efetivo, repr, enums
│   ├── test_projecao.py         # 15 testes — projeção de saldo dia a dia
│   ├── test_conciliacao.py      # 19 testes — motor conciliação (dicionário/fuzzy/keywords)
│   └── test_importacao.py       # 21 testes — parser CSV/OFX + detecção formato
│
├── alembic/
│   ├── env.py                   # Importa todos os models, usa DATABASE_URL_SYNC
│   ├── script.py.mako
│   └── versions/.gitkeep        # ⚠️  Sem migrações geradas ainda
│
├── scripts/
│   ├── __init__.py
│   └── seed.py                  # 24 categorias iniciais (idempotente)
│
├── requirements.txt             # 18 dependências (inclui aiosqlite para testes)
├── pytest.ini                   # asyncio_mode = auto
├── alembic.ini
├── Dockerfile                   # Multi-stage build (python:3.11-slim)
├── docker-compose.yml           # app + postgres:16-alpine, network host build
├── entrypoint.sh                # Wait DB + seed + uvicorn
├── .dockerignore                # Exclui .venv, tests, .git, .prompts
├── .github/
│   └── copilot-instructions.md  # Convenções de dev para GitHub Copilot
├── README.md
└── prompt-prd.md                # PRD completo
```

---

## 3. O Que Está Implementado (Must Have do PRD)

| Feature do PRD                              | Status | Localização                                      |
|---------------------------------------------|--------|--------------------------------------------------|
| Dashboard Visual (gráfico projeção)         | ✅     | `routers/dashboard.py` · `templates/dashboard.html` |
| Gráfico: linha sólida (real) + pontilhada   | ✅     | Chart.js no `dashboard.html` (JS inline)          |
| Tooltips interativos com composição diária   | ✅     | Chart.js tooltip callback                         |
| Calendário financeiro mensal                 | ✅     | `partials/calendario.html` — corrigido alinhamento |
| Cards resumo (saldo atual, fim mês, negativos)| ✅    | `routers/dashboard.py` + `dashboard.html`         |
| Gestão de Transações (CRUD completo)         | ✅     | `routers/transacoes.py` (7 endpoints)             |
| Entrada Rápida (FAB global)                  | ✅     | `base.html` — botão flutuante + modal HTMX       |
| Ciclo Projetada → Executada                  | ✅     | `models/transacao.py` (enum StatusTransacao)      |
| Classificação (Fixa/Recorrente/Variável/Espor.) | ✅     | `models/categoria.py` (enum NaturezaCategoria)    |
| Importação OFX                               | ✅     | `services/importacao.py` (ofxparse)               |
| Importação CSV                               | ✅     | `services/importacao.py` (configurável, defaults MercadoPago) |
| Descrição editável na conciliação            | ✅     | `partials/conciliacao_lista.html` (input + sync hidden) |
| Detecção de duplicatas na importação         | ✅     | `routers/importacao.py` + `schemas/conciliacao.py` |
| Motor Conciliação: Dicionário (exato)        | ✅     | `services/conciliacao.py` → `_match_dicionario`   |
| Motor Conciliação: Fuzzy (data±3d, valor±5%) | ✅     | `services/conciliacao.py` → `_match_fuzzy`        |
| Motor Conciliação: Palavras-chave (fallback) | ✅     | `services/conciliacao.py` → `_match_palavras_chave`|
| Loop de Aprendizado (dicionário)             | ✅     | `confirmar_conciliacao` → salva em `DicionarioConciliacao`|
| CRUD Contas                                  | ✅     | `routers/contas.py` (5 endpoints)                 |
| CRUD Categorias                              | ✅     | `routers/categorias.py` (6 endpoints: CRUD + PUT + options) |
| Seed de categorias iniciais (24)             | ✅     | `scripts/seed.py`                                 |
| Testes unitários + integração                | ✅     | 155/155 passando, 0 warnings                     |
| Projeção inteligente (fixas+recorrentes)     | ✅     | `services/projecao.py` — gera transações virtuais  |
| Selector de dias para projeção             | ✅     | `routers/dashboard.py` + `dashboard.html`         |
| Parcelas em transações recorrentes          | ✅     | `models/transacao.py` (parcela_atual, total_parcelas) |
| Projeção variável por média mensal          | ✅     | `services/projecao.py` — média da categoria          |
| Natureza Esporádica (não projeta)           | ✅     | `models/categoria.py` + `services/projecao.py`       |

---

## 4. Testes — Status Atual

```
tests/test_api.py            — 40 passed ✅  (integração HTTP: contas, categorias, transações, dashboard, importação)
tests/test_schemas.py        — 22 passed ✅  (validação Pydantic)
tests/test_models.py         — 17 passed ✅  (valor_efetivo, repr, enums — inclui Esporádica)
tests/test_projecao.py       — 45 passed ✅  (projeção saldo + virtuais fixas/recorrentes/variáveis/esporádicas + média mensal)
tests/test_conciliacao.py    — 19 passed ✅  (motor conciliação)
tests/test_importacao.py     — 21 passed ✅  (parser CSV/OFX)
tests/conftest.py            — fixtures (SQLite in-memory + AsyncClient)
=============================================
TOTAL: 168 passed, 0 failed, 0 warnings
```

### Cobertura dos testes:

**API (integração HTTP):** CRUD contas (criar, listar, editar, deletar, inexistente), CRUD categorias (criar despesa/receita, listar, editar, edição parcial, deletar, inexistente, options + filtro tipo), CRUD transações (criar despesa/receita, form nova/editar, atualizar, deletar, inexistente), dashboard (sem contas, com conta, seleção, projeção, calendário + alinhamento, projeção com transações), importação (página, upload CSV, conciliação, confirmar individual/todas).

**Schemas:** Validação dos 4 domínios (conta, categoria, transação, conciliação) — campos obrigatórios, defaults, rejeição de inválidos, update parcial, from_attributes.

**Models:** valor_efetivo (executada com/sem realizado, projetada, zero, receita), repr dos 4 models, enums (values, tipo string, contagem membros).

**Projeção:** sem transações, com despesa, com receita, múltiplas no mesmo dia, saldo negativo, tipo real/projetado, movimentação diária, acumulação antes do período, arredondamento 2 casas, período único dia, saldo zero, transações antes+durante, valores grandes, saldo inicial negativo, movimentação zero, **despesa fixa projeta meses futuros, recorrente projeta parcelas, variável não projeta, dedup mes existente, sem categoria não projeta, recorrente sem parcelas, última parcela, ajuste dia mês curto, múltiplas fixas independentes, receita fixa positiva, _gerar_virtuais isolado, descrição parcela, _add_months (básico, fim mês curto, bissexto, virada ano, múltiplos)**.

**Conciliação:** match dicionário (exato + sem), fuzzy (valor+data exatos, tolerância data ±3d, tolerância valor ±5%, fora tolerância, melhor candidato), palavras-chave (match + sem), prioridade dicionário > fuzzy, transação nova, edge cases (whitespace, valor zero, match perfeito, janela dias, case insensitive, preservação, prioridade fuzzy > keywords).

**Importação:** CSV (básico BR, ponto milhar, linhas inválidas, vazio, sem cabeçalho, delimitador custom, formato data, encoding latin1, colunas custom, centavos), OFX (básico, payee fallback, vazio, sem statement, date como date, múltiplas contas), detecção formato (ofx, csv, erro, caminho, sem extensão).

---

## 5. Bugs Conhecidos e Débitos Técnicos

### 🔴 Bugs

1. ~~**Calendário desalinhado**~~ — ✅ Corrigido. `primeiro_weekday` calculado no backend e passado ao template. Grid agora renderiza divs vazias antes do dia 1.

### 🟡 Débitos Técnicos

2. ~~**Alembic sem migrações**~~ — ✅ Resolvido. Migrations geradas (parcelas + enum Esporádica) e `entrypoint.sh` executa `alembic upgrade head` no startup.

3. ~~**Sem testes de integração HTTP**~~ — ✅ Resolvido. 40 testes de integração HTTP via `httpx.AsyncClient` com SQLite in-memory.

4. ~~**PUT de categorias não implementado**~~ — ✅ Corrigido. Endpoint PUT adicionado em `routers/categorias.py`.

5. ~~**Deprecação Pydantic**~~ — ✅ Corrigido. `app/config.py` usa `ConfigDict` em vez de `class Config:`. Warning residual vem do `pydantic-settings` internamente (fora do nosso controle).

6. **`descricao_banco` no model Transacao** — Campo adicional não previsto no PRD (seção 6), mas útil. Adicionado como extensão.

7. ~~**Enum StatusTransacao desalinhado com PostgreSQL**~~ — ✅ Corrigido via `values_callable`. SQLAlchemy agora armazena os values (`Projetada`/`Executada`) e não os names (`PROJETADA`/`EXECUTADA`). ⚠️ **ATENÇÃO:** Se houver dados existentes no PostgreSQL com nomes antigos, será necessária uma migration de dados para alinhar.

8. ~~**Starlette TemplateResponse deprecation**~~ — ✅ Corrigido. 20 ocorrências em 5 routers migradas de `TemplateResponse(name, {"request": request, ...})` para `TemplateResponse(request, name, context)`. Zero warnings nos testes.

---

## 6. O Que Falta Fazer (Roadmap)

### Prioridade Alta (corrigir o que existe)

- [x] Corrigir alinhamento do calendário (preencher dias vazios antes do dia 1 com base no weekday)
- [x] Gerar primeira migration Alembic
- [x] Adicionar endpoint PUT `/categorias/{id}` para edição

### Prioridade Média (robustez)

- [x] Testes de integração HTTP com `httpx.AsyncClient` (testar endpoints)
- [ ] Tratamento de erros mais robusto nos routers (try/except, mensagens amigáveis)
- [ ] Validação de dados no frontend (HTMX + HTML5 validation)
- [ ] Paginação na lista de transações (hoje carrega todas do mês)

### Should Have (PRD v1.1+)

- [ ] Importação de dados financeiros via `.pdf`
- [ ] Exportação dos dados consolidados para `.csv`
- [ ] Gráficos secundários de distribuição (pizza/barras por categoria no mês)

### Nice to Have (melhorias UX)

- [x] Recorrência automática de transações (gerar projetadas futuras)
- [ ] Dark mode
- [ ] Busca/filtro por descrição nas transações
- [ ] Confirmação visual mais clara no calendário (tooltip com detalhes)
- [ ] Mobile responsiveness refinado

---

## 7. Configurações e Constantes Importantes

### Motor de Conciliação (`services/conciliacao.py`)
```python
TOLERANCIA_DIAS = 3               # Janela de busca fuzzy: ±3 dias
TOLERANCIA_VALOR_PERCENTUAL = 0.05 # Margem de valor: ±5%
SCORE_MINIMO_FUZZY = 50            # Score mínimo para match fuzzy
SCORE_MINIMO_PALAVRAS = 50         # Score mínimo para match por palavras-chave
```

### Scoring do Fuzzy
- **Valor:** 0-50 pontos (proporcional à proximidade do valor)
- **Data:** 0-30 pontos (30 - diff_dias × 10)
- **Texto:** 0-20 pontos (token_sort_ratio / 100 × 20)
- **Total:** 0-100 pontos

### Enums do sistema
```python
TipoCategoria:    Receita | Despesa
NaturezaCategoria: Fixa | Recorrente | Variável | Esporádica
StatusTransacao:   Projetada | Executada
```

### CSV Import (defaults — corrigido para MercadoPago)
```python
encoding="utf-8", delimitador=";", col_data=0, col_descricao=1,
col_valor=3, formato_data="%d-%m-%Y", pular_cabecalho=True
```

---

## 8. Como Rodar

### Opção A — Docker (recomendado) 🐳

```bash
# Subir tudo (app + PostgreSQL)
cd willu && docker compose up --build -d

# Verificar status
docker compose ps
docker compose logs app --tail 30

# Acessar
# http://localhost:8000

# Parar
docker compose down

# Parar e apagar volume do banco
docker compose down -v
```

> **Nota WSL:** O Docker Desktop pode não estar disponível. Nesse caso, iniciar o daemon manualmente:
> ```bash
> sudo dockerd --iptables=false > /tmp/dockerd.log 2>&1 &
> ```

### Opção B — Local (dev)

```bash
# Setup
cd willu && source .venv/bin/activate

# Testes (não precisa de banco)
pytest tests/ -v

# App (precisa PostgreSQL com banco willu_financas)
python -m scripts.seed          # popular categorias iniciais
uvicorn app.main:app --reload   # http://localhost:8000
```

### Dependências instaladas (.venv ativo)
FastAPI 0.115, SQLAlchemy 2.0.35, asyncpg 0.29, Pydantic 2.9.2, pydantic-settings 2.5.2, Jinja2 3.1.4, HTMX 2.0.2 (CDN), Tailwind (CDN), Chart.js 4.4.4 (CDN), thefuzz 0.22.1, ofxparse 0.21, pytest 8.3.3, aiosqlite 0.22.1, httpx (para testes)

---

## 9. Decisões de Arquitetura Tomadas

1. **HTML over the wire** — Templates Jinja2 + HTMX em vez de SPA. Partials retornam HTML fragmentado para swaps dinâmicos.
2. **CDN para CSS/JS** — Tailwind e Chart.js via CDN (sem build step). Simplifica o setup.
3. **Funções `_sync`** — Cada serviço tem versão síncrona pura para testes unitários sem banco, além da versão async para produção.
4. **FAB global** — Botão flutuante em `base.html` dispara HTMX GET para carregar form no modal, disponível em todas as páginas.
5. **Auto-create tables** — `Base.metadata.create_all` no lifespan para dev. Alembic configurado para produção.
6. **Despesas como valores negativos** — Transações de despesa são armazenadas como valores negativos no banco. O form converte automaticamente.
7. **Docker multi-stage build** — Builder stage com gcc+libpq-dev para compilar deps; runtime stage leve com libpq5+curl apenas. Imagem final ~200MB.
8. **`network: host` no build** — Necessário no WSL onde a rede bridge do Docker não resolve DNS externo durante o build.
9. **Entrypoint com wait-for-db** — `entrypoint.sh` usa socket Python para aguardar PostgreSQL antes de rodar seed e uvicorn. Mais portável que `wait-for-it.sh`.
10. **Hot-reload com volume + `--reload`** — `docker-compose.yml` monta `./app:/app/app` e passa `UVICORN_ARGS="--reload"` para que alterações em código Python e templates reflitam automaticamente no container sem rebuild.

---

## 10. Changelog — Sessão 2026-02-28

### 🐛 Bug Fixes

1. **CSV MercadoPago: coluna do valor errada** — `col_valor` mudou de `2` → `3` (a coluna `TRANSACTION_NET_AMOUNT` é índice 3). Arquivo: `services/importacao.py`.
2. **CSV MercadoPago: formato de data errado** — `formato_data` mudou de `"%d/%m/%Y"` → `"%d-%m-%Y"` (datas com hífen). Arquivo: `services/importacao.py`.
3. **Detecção de duplicatas não funcionava** — A query filtrava por `StatusTransacao.EXECUTADA` mas o enum Python envia `"Executada"` enquanto o PostgreSQL armazena `"EXECUTADA"`. Removido filtro por status (desnecessário) e adicionada comparação case-insensitive com `func.lower(func.trim(...))`. Arquivo: `routers/importacao.py`.
4. **Código Python não recarregava no container** — O uvicorn rodava sem `--reload`, então o volume montado só atualizava templates (Jinja2 re-lê a cada request), mas não código Python. Adicionado `UVICORN_ARGS: "--reload"` no `docker-compose.yml`.

---

## 11. Changelog — Sessão 2026-03-07

### 🐛 Bug Fixes

1. **Calendário desalinhado** — Template `partials/calendario.html` tentava calcular weekday em Jinja2 com lógica incompleta. Corrigido: `primeiro_weekday` agora é calculado no Python (`date.weekday()`) em `routers/dashboard.py` e passado ao template que renderiza divs vazias antes do dia 1.

2. **Enum desalinhado com PostgreSQL** — `StatusTransacao`, `TipoCategoria` e `NaturezaCategoria` armazenavam os names dos enums (ex: `EXECUTADA`) no banco em vez dos values (ex: `Executada`). Adicionado `values_callable=lambda x: [e.value for e in x]` nos 3 campos `Enum()` em `models/transacao.py` e `models/categoria.py`. ⚠️ Dados existentes no PostgreSQL precisam de migration de dados.

3. **Deprecação Pydantic `class Config:`** — `app/config.py` migrado de `class Config: env_file = ".env"` para `model_config = ConfigDict(env_file=".env")`. Warning residual é do `pydantic-settings` internamente.

4. **Deprecação Starlette TemplateResponse** — 20 ocorrências em 5 routers (`contas.py`, `dashboard.py`, `categorias.py`, `transacoes.py`, `importacao.py`) migradas de `TemplateResponse(name, {"request": request, ...})` para `TemplateResponse(request, name, context)`. 63 warnings eliminados.

### ✨ Melhorias

5. **Endpoint PUT `/categorias/{id}`** — Schema `CategoriaUpdate` existia mas o endpoint não. Adicionado com suporte a atualização parcial (nome, tipo, natureza).

6. **Expansão massiva de testes: 27 → 138** — Criados `tests/conftest.py` (fixtures SQLite in-memory), `tests/test_api.py` (40 testes de integração HTTP), `tests/test_schemas.py` (22 testes), `tests/test_models.py` (17 testes). Expandidos `test_importacao.py` (7→21), `test_projecao.py` (9→15), `test_conciliacao.py` (11→19).

7. **Convenções de desenvolvimento** — Criado `.github/copilot-instructions.md` com regras de gerenciamento de dependências, TDD, código Python, templates, Docker, e progresso.

8. **`aiosqlite` no requirements.txt** — Dependência para testes com SQLite async adicionada ao `requirements.txt`.

### 📁 Arquivos Alterados/Criados

| Arquivo | Mudança |
|---|---|
| `app/templates/partials/calendario.html` | Removida lógica Jinja2 de weekday, usa `primeiro_weekday` do backend |
| `app/routers/dashboard.py` | Calcula `primeiro_weekday` + TemplateResponse nova assinatura |
| `app/config.py` | `class Config:` → `model_config = ConfigDict(env_file=".env")` |
| `app/routers/categorias.py` | Novo endpoint PUT + TemplateResponse nova assinatura |
| `app/models/transacao.py` | `values_callable` no Enum StatusTransacao |
| `app/models/categoria.py` | `values_callable` nos Enums TipoCategoria e NaturezaCategoria |
| `app/routers/contas.py` | TemplateResponse nova assinatura (5 ocorrências) |
| `app/routers/transacoes.py` | TemplateResponse nova assinatura (4 ocorrências) |
| `app/routers/importacao.py` | TemplateResponse nova assinatura (2 ocorrências) |
| `tests/conftest.py` | **NOVO** — Fixtures SQLite in-memory + AsyncClient |
| `tests/test_api.py` | **NOVO** — 40 testes integração HTTP |
| `tests/test_schemas.py` | **NOVO** — 22 testes validação Pydantic |
| `tests/test_models.py` | **NOVO** — 17 testes models |
| `tests/test_importacao.py` | Expandido 7→21 testes |
| `tests/test_projecao.py` | Expandido 9→15 testes |
| `tests/test_conciliacao.py` | Expandido 11→19 testes |
| `.github/copilot-instructions.md` | **NOVO** — Convenções de desenvolvimento |
| `requirements.txt` | Adicionado `aiosqlite==0.22.1` |

### ✨ Melhorias

5. **Hot-reload com Docker volume** — Adicionado `volumes: ["./app:/app/app"]` no `docker-compose.yml` para evitar rebuild a cada mudança de código.
6. **Descrição editável na importação** — Na tela de conciliação (`partials/conciliacao_lista.html`), a descrição agora mostra um input editável com a sugestão (ou descrição do banco), e a descrição original do banco em texto pequeno como referência. Funciona tanto para confirmação individual (sincroniza hidden field) quanto para "Confirmar Todas" (lê do input).
7. **Detecção de duplicatas na importação** — Ao importar extrato, cada linha é comparada com transações já existentes no banco (mesma `data_pagamento`, `descricao_banco` case-insensitive e `valor_realizado` com tolerância de R$ 0,01). Duplicatas aparecem com fundo amarelo, badge "⚠️ Duplicada" e botão "✕ Excluir" para remover da lista. Schema `SugestaoConciliacao` ganhou campo `duplicada: bool = False`.

### 📁 Arquivos Alterados

| Arquivo | Mudança |
|---|---|
| `services/importacao.py` | `col_valor=3`, `formato_data="%d-%m-%Y"` |
| `docker-compose.yml` | Volume `./app:/app/app` + `UVICORN_ARGS: "--reload"` |
| `schemas/conciliacao.py` | Campo `duplicada: bool = False` em `SugestaoConciliacao` |
| `routers/importacao.py` | Lógica de detecção de duplicatas (query sem filtro de status, case-insensitive) |
| `templates/partials/conciliacao_lista.html` | Input editável para descrição + UI de duplicatas (badge + botão excluir) |

---

## 12. Changelog — Sessão 2026-03-07 (Projeção Inteligente)

### ✨ Features

1. **Projeção inteligente de saldo com despesas fixas e recorrentes** — O serviço `services/projecao.py` agora gera transações virtuais futuras:
   - **Despesas Fixas (natureza=Fixa):** repetem mensalmente no mesmo dia do mês, indefinidamente, até o fim do período de projeção. Ex: Aluguel dia 5 → projeta dia 5 de cada mês futuro.
   - **Despesas Recorrentes (natureza=Recorrente):** usam `parcela_atual` e `total_parcelas` para calcular quantas parcelas restam e projetá-las mensalmente. Ex: Notebook parcela 3/12 → projeta parcelas 4 a 12.
   - **Despesas Variáveis:** não geram projeções, aparecem apenas quando lançadas.
   - **Dedup:** não duplica meses que já possuem transação real para a mesma (categoria_id, descricao).
   - Ajuste automático para meses mais curtos (ex: dia 31 → dia 28 em fevereiro).

2. **Seletor de dias para projeção** — O dashboard agora permite escolher o horizonte de projeção: 30, 60, 90, 180 dias ou 1 ano. Parâmetro `dias_futuro` substitui o antigo `meses`.

3. **Campos de parcela no model Transacao** — Adicionados `parcela_atual` e `total_parcelas` (ambos opcionais) ao model, schemas e formulário de transação. O form exibe os campos de parcela apenas quando a categoria selecionada é "Recorrente".

4. **Função `_add_months`** — Helper para adicionar N meses a uma data com ajuste automático do dia para meses mais curtos (ex: Jan 31 + 1 mês = Feb 28).

5. **Função `_gerar_virtuais`** — Core da lógica de projeção. Recebe transações reais e gera virtuais futuros baseados na natureza da categoria. Usado tanto pela versão async quanto pela sync.

### 📊 Testes

6. **Expansão de testes de projeção: 15 → 32** — 17 novos testes cobrindo:
   - `TestAddMonths` (5 testes): básico, fim mês curto, ano bissexto, virada de ano, múltiplos meses.
   - `TestProjecaoVirtuais` (12 testes): fixa projeta futuros, recorrente projeta parcelas, variável não projeta, dedup mês existente, sem categoria, recorrente sem parcelas, última parcela, ajuste dia mês curto, múltiplas fixas independentes, receita fixa positiva, `_gerar_virtuais` isolado, descrição com número de parcela.

### 📁 Arquivos Alterados

| Arquivo | Mudança |
|---|---|
| `app/models/transacao.py` | Adicionados `parcela_atual: int \| None` e `total_parcelas: int \| None` |
| `app/schemas/transacao.py` | Campos `parcela_atual` e `total_parcelas` em Create/Update/Read |
| `app/services/projecao.py` | Reescrito: `_add_months`, `_gerar_virtuais`, projeção com virtuais, `selectinload(categoria)` |
| `app/routers/dashboard.py` | `meses` → `dias_futuro`, passa `dias_futuro` ao template |
| `app/routers/transacoes.py` | Criação e atualização de transações com campos de parcela |
| `app/templates/dashboard.html` | Seletor de dias (30/60/90/180/365), preserva `dias_futuro` na URL |
| `app/templates/partials/transacao_form.html` | Campos de parcela (visíveis quando categoria=Recorrente), JS toggle |
| `tests/test_projecao.py` | 15 → 32 testes (3 classes: TestAddMonths, TestProjecaoVirtuais + existentes) |
| `.prompts/progresso.md` | Atualizado com changelog e contagens |

---

## 13. Changelog — Sessão 2026-03-07 (Variáveis + Esporádica)

### ✨ Features

1. **Projeção de despesas variáveis por média mensal** — Categorias com natureza "Variável" (ex: Alimentação, Supermercado, Transporte) agora projetam para meses futuros usando a média dos totais mensais históricos daquela categoria. A projeção aparece no dia 15 de cada mês futuro. Meses incompletos (mês atual) são excluídos do cálculo; se só há dados do mês corrente, usa como fallback. Transações de descrições diferentes são agrupadas pela `categoria_id`.

2. **Nova natureza "Esporádica"** — Adicionada ao enum `NaturezaCategoria`. Despesas esporádicas (ex: presentes, viagens, lazer) **não geram projeções futuras**. Isso separa gastos imprevisíveis/únicos (Esporádica) dos gastos variáveis mas recorrentes e previsíveis (Variável).

3. **Função `_calcular_media_mensal`** — Helper que agrupa transações por (ano, mês), soma os valores de cada mês, exclui o mês corrente (incompleto), e retorna a média dos totais mensais.

4. **Seed atualizado com Esporádica** — Categorias de despesa reclassificadas:
   - **Variável** (projetável): Alimentação, Supermercado, Transporte, Saúde
   - **Esporádica** (não projetável): Lazer, Vestuário, Educação, Presentes, Viagens, Outros
   - Adicionadas categorias novas: "Presentes" e "Viagens" (26 categorias no seed)

5. **Migration Alembic para enum** — Gerada migration que executa `ALTER TYPE naturezacategoria ADD VALUE IF NOT EXISTS 'Esporádica'` no PostgreSQL.

### 📊 Testes

6. **Expansão de testes de projeção: 32 → 45** — 13 novos testes:
   - `TestProjecaoEsporadica` (3 testes): esporádica não projeta, `_gerar_virtuais` retorna vazio, mix esporádica+fixa independentes.
   - `TestProjecaoVariavelMedia` (5 testes): média de 2 meses, fallback mês atual, agrupamento por categoria, não duplica mêses com real, receita variável positiva.
   - `TestCalcularMediaMensal` (5 testes): média básica, exclui mês atual, fallback mês atual, sem transações, múltiplas no mesmo mês.
   - `test_despesa_variavel_nao_projeta` → renomeado para `test_despesa_variavel_projeta_media`.

### 📁 Arquivos Alterados

| Arquivo | Mudança |
|---|---|
| `app/models/categoria.py` | `NaturezaCategoria.ESPORADICA = "Esporádica"` adicionado |
| `app/services/projecao.py` | `_gerar_virtuais` com lógica Variável (média) e Esporádica (skip); `_calcular_media_mensal` |
| `scripts/seed.py` | Reclassificação: Lazer/Vestuário/Educação/Outros → Esporádica; +Presentes, +Viagens |
| `tests/test_projecao.py` | 32 → 45 testes (+3 Esporádica, +5 Variável, +5 Média) |
| `tests/test_models.py` | Enum Esporádica no test_natureza + contagem 3→4 |
| `alembic/versions/929353c776fe_*.py` | Migration: ALTER TYPE naturezacategoria ADD VALUE 'Esporádica' |
| `.prompts/progresso.md` | Atualizado com changelog e contagens |
