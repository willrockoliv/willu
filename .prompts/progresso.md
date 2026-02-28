# 📋 Willu — Registro de Progresso

> Última atualização: 2026-02-28 (Docker adicionado)
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
│   ├── test_projecao.py         # 9 testes — projeção de saldo dia a dia
│   ├── test_conciliacao.py      # 11 testes — motor conciliação (dicionário/fuzzy/keywords)
│   └── test_importacao.py       # 7 testes — parser CSV + detecção formato
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
├── .env.example                 # Modelo de variáveis de ambiente
├── .env                         # Cópia local (gitignored)
├── requirements.txt             # 17 dependências
├── pytest.ini                   # asyncio_mode = auto
├── alembic.ini
├── Dockerfile                   # Multi-stage build (python:3.11-slim)
├── docker-compose.yml           # app + postgres:16-alpine, network host build
├── entrypoint.sh                # Wait DB + seed + uvicorn
├── .dockerignore                # Exclui .venv, tests, .git, .prompts
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
| Calendário financeiro mensal                 | ⚠️     | `partials/calendario.html` — ver bugs abaixo     |
| Cards resumo (saldo atual, fim mês, negativos)| ✅    | `routers/dashboard.py` + `dashboard.html`         |
| Gestão de Transações (CRUD completo)         | ✅     | `routers/transacoes.py` (7 endpoints)             |
| Entrada Rápida (FAB global)                  | ✅     | `base.html` — botão flutuante + modal HTMX       |
| Ciclo Projetada → Executada                  | ✅     | `models/transacao.py` (enum StatusTransacao)      |
| Classificação (Fixa/Recorrente/Variável)     | ✅     | `models/categoria.py` (enum NaturezaCategoria)    |
| Importação OFX                               | ✅     | `services/importacao.py` (ofxparse)               |
| Importação CSV                               | ✅     | `services/importacao.py` (configurável BR)        |
| Motor Conciliação: Dicionário (exato)        | ✅     | `services/conciliacao.py` → `_match_dicionario`   |
| Motor Conciliação: Fuzzy (data±3d, valor±5%) | ✅     | `services/conciliacao.py` → `_match_fuzzy`        |
| Motor Conciliação: Palavras-chave (fallback) | ✅     | `services/conciliacao.py` → `_match_palavras_chave`|
| Loop de Aprendizado (dicionário)             | ✅     | `confirmar_conciliacao` → salva em `DicionarioConciliacao`|
| CRUD Contas                                  | ✅     | `routers/contas.py` (5 endpoints)                 |
| CRUD Categorias                              | ✅     | `routers/categorias.py` (5 endpoints)             |
| Seed de categorias iniciais (24)             | ✅     | `scripts/seed.py`                                 |
| Testes unitários (projeção + conciliação)    | ✅     | 27/27 passando                                    |

---

## 4. Testes — Status Atual

```
tests/test_projecao.py      —  9 passed ✅
tests/test_conciliacao.py   — 11 passed ✅
tests/test_importacao.py    —  7 passed ✅
========================================
TOTAL: 27 passed, 0 failed
```

### Cobertura dos testes:

**Projeção:** sem transações, com despesa, com receita, múltiplas no mesmo dia, saldo negativo, tipo real/projetado, movimentação diária, acumulação antes do período, arredondamento 2 casas.

**Conciliação:** match dicionário (exato + sem), fuzzy (valor+data exatos, tolerância data ±3d, tolerância valor ±5%, fora tolerância, melhor candidato), palavras-chave (match + sem), prioridade dicionário > fuzzy, transação nova.

**Importação:** CSV básico BR, valores com ponto milhar, linhas inválidas (skip), CSV vazio, detecção formato (OFX/CSV/erro).

---

## 5. Bugs Conhecidos e Débitos Técnicos

### 🔴 Bugs

1. **Calendário desalinhado** — `partials/calendario.html` (linhas ~51-56) tem lógica incompleta para calcular o weekday do 1° dia do mês. Os dias vazios antes do dia 1 não são renderizados, fazendo o grid 7 colunas ficar desalinhado com os headers (Seg-Dom).

### 🟡 Débitos Técnicos

2. **Alembic sem migrações** — Infraestrutura configurada (`alembic/env.py` importa todos os models) mas nenhuma migration foi gerada. O app cria tabelas via `Base.metadata.create_all` no startup (dev mode). Precisa rodar `alembic revision --autogenerate` para produção.

3. **Sem testes de integração HTTP** — `httpx` está instalado mas não há testes usando `AsyncClient` contra os endpoints FastAPI. Só testes das funções `_sync`.

4. **PUT de categorias não implementado** — O schema `CategoriaUpdate` existe mas o router `/categorias/{id}` PUT não tem endpoint. Só tem create e delete.

5. **Deprecação Pydantic** — `app/config.py` usa `class Config:` em vez de `ConfigDict`. Gera warning no pytest. Baixa severidade.

6. **`descricao_banco` no model Transacao** — Campo adicional não previsto no PRD (seção 6), mas útil. Adicionado como extensão.

---

## 6. O Que Falta Fazer (Roadmap)

### Prioridade Alta (corrigir o que existe)

- [ ] Corrigir alinhamento do calendário (preencher dias vazios antes do dia 1 com base no weekday)
- [ ] Gerar primeira migration Alembic (`alembic revision --autogenerate -m "initial"`)
- [ ] Adicionar endpoint PUT `/categorias/{id}` para edição

### Prioridade Média (robustez)

- [ ] Testes de integração HTTP com `httpx.AsyncClient` (testar endpoints)
- [ ] Tratamento de erros mais robusto nos routers (try/except, mensagens amigáveis)
- [ ] Validação de dados no frontend (HTMX + HTML5 validation)
- [ ] Paginação na lista de transações (hoje carrega todas do mês)

### Should Have (PRD v1.1+)

- [ ] Importação de dados financeiros via `.pdf`
- [ ] Exportação dos dados consolidados para `.csv`
- [ ] Gráficos secundários de distribuição (pizza/barras por categoria no mês)

### Nice to Have (melhorias UX)

- [ ] Recorrência automática de transações (gerar projetadas futuras)
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
NaturezaCategoria: Fixa | Recorrente | Variável
StatusTransacao:   Projetada | Executada
```

### CSV Import (defaults)
```python
encoding="utf-8", delimitador=";", col_data=0, col_descricao=1,
col_valor=2, formato_data="%d/%m/%Y", pular_cabecalho=True
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
FastAPI 0.115, SQLAlchemy 2.0.35, asyncpg 0.29, Pydantic 2.9.2, Jinja2 3.1.4, HTMX 2.0.2 (CDN), Tailwind (CDN), Chart.js 4.4.4 (CDN), thefuzz 0.22.1, ofxparse 0.21, pytest 8.3.3

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
