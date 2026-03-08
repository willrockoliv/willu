# 💰 Willu - Finanças Pessoais

Aplicação web de finanças pessoais com foco em **projeção de saldo futuro** e **conciliação inteligente de extratos bancários**.

## ✨ Funcionalidades

- 📊 **Dashboard Visual** — Gráfico de projeção diária de saldo (linha sólida para passado, pontilhada para futuro)
- 📅 **Calendário Financeiro** — Visão mensal com alertas para dias negativos ou de alto impacto
- 🔮 **Projeção Inteligente** — Transações fixas repetem mensalmente, recorrentes projetam parcelas restantes, variáveis usam média mensal histórica
- ➕ **Entrada Rápida** — FAB (Floating Action Button) para cadastro ágil de transações
- 📂 **Importação de Extratos** — Suporte para arquivos `.ofx` e `.csv` com detecção de duplicatas
- 🧠 **Conciliação Inteligente** — Motor de matching: Dicionário → Fuzzy → Palavras-chave
- 🔄 **Aprendizado Contínuo** — Cada confirmação alimenta o dicionário para automatizar futuras importações
- 🌙 **Dark Mode** — Toggle com persistência em `localStorage` e detecção automática da preferência do sistema
- 🏷️ **Classificação por Natureza** — Fixa, Recorrente, Variável e Esporádica (com comportamento diferente na projeção)
- 📦 **Parcelas** — Suporte a transações parceladas com controle de parcela atual e total

## 🛠 Stack Tecnológica

| Componente | Tecnologia |
|-----------|-----------|
| Backend | Python 3.11 · FastAPI |
| Banco de Dados | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Frontend | Jinja2 · HTMX · Tailwind CSS (CDN) |
| Gráficos | Chart.js |
| Testes | pytest · pytest-asyncio · httpx |
| Conciliação | thefuzz (fuzzy matching) · ofxparse |

## 🚀 Instalação e Setup

### Opção A — Docker (recomendado) 🐳

Pré-requisitos: Docker e Docker Compose.

```bash
cd willu
docker compose up --build -d
```

> **WSL sem Docker Desktop:** se o daemon não estiver ativo é possível que receba a seguinte mensagem de erro:
> ```bash
> Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?
> ```
> Caso isso ocorra, inicie-o manualmente:
> ```bash
> sudo dockerd --iptables=false &
> ```

Isso sobe automaticamente:
- **PostgreSQL 16** com banco `willu_financas` pronto
- **App FastAPI** com seed de categorias e uvicorn

Acesse: **http://localhost:8000**

Para verificar status:
```bash
docker compose ps
docker compose logs app --tail 30
```

Para parar:
```bash
docker compose down
```

Para parar e apagar dados do banco:
```bash
docker compose down -v
```

---

### Opção B — Local (dev)

Pré-requisitos: Python 3.11+ e PostgreSQL 14+.

#### 1. Instalar dependências

```bash
cd willu
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 2. Configurar banco de dados

Crie o banco no PostgreSQL:

```sql
CREATE DATABASE willu_financas;
```

Copie e edite as variáveis de ambiente:

```bash
cp .env.example .env
# Edite .env com suas credenciais do PostgreSQL
```

#### 3. Rodar migrations

```bash
alembic upgrade head
```

Ou, no modo desenvolvimento, as tabelas são criadas automaticamente no startup.

#### 4. Popular dados iniciais (categorias)

```bash
python -m scripts.seed
```

> O seed é idempotente e cria 24 categorias iniciais (Receitas + Despesas classificadas por natureza).

#### 5. Rodar a aplicação

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Acesse: **http://localhost:8000**

## 🧪 Testes

```bash
pytest tests/ -v
```

**168 testes passando, 0 warnings:**

| Arquivo | Testes | Escopo |
|---------|--------|--------|
| `test_api.py` | 40 | Integração HTTP — CRUD contas, categorias, transações, dashboard, importação |
| `test_projecao.py` | 45 | Projeção de saldo — fixas, recorrentes, variáveis (média), esporádicas, `_add_months` |
| `test_schemas.py` | 22 | Validação Pydantic — campos obrigatórios, defaults, rejeição de inválidos |
| `test_importacao.py` | 21 | Parser CSV/OFX — encoding, delimitadores, formatos de data, detecção |
| `test_conciliacao.py` | 19 | Motor conciliação — dicionário, fuzzy, palavras-chave, prioridades |
| `test_models.py` | 17 | Models — `valor_efetivo`, `repr`, enums (incluindo Esporádica) |

> Testes unitários usam funções `_sync` (sem banco). Testes de integração usam SQLite in-memory via fixtures do `conftest.py`.

## 📁 Estrutura do Projeto

```
willu/
├── app/
│   ├── main.py                  # Entrypoint FastAPI, lifespan cria tabelas
│   ├── config.py                # Settings via pydantic-settings + .env
│   ├── database.py              # Engine async + sessionmaker + Base + get_db
│   ├── models/
│   │   ├── conta.py             # Conta (id, nome, saldo_inicial)
│   │   ├── categoria.py         # Categoria (id, nome, tipo, natureza) + enums
│   │   ├── transacao.py         # Transacao (ciclo Projetada→Executada) + parcelas
│   │   └── dicionario_conciliacao.py  # Aprendizado de conciliação
│   ├── schemas/                 # Schemas Pydantic (Create, Update, Read)
│   ├── routers/
│   │   ├── dashboard.py         # GET / (dashboard), /api/projecao, /api/calendario
│   │   ├── contas.py            # CRUD /contas/
│   │   ├── categorias.py        # CRUD /categorias/ + /categorias/options
│   │   ├── transacoes.py        # CRUD /transacoes/ + modal form
│   │   └── importacao.py        # /importacao/ + upload + confirmar + confirmar-todas
│   ├── services/
│   │   ├── projecao.py          # Projeção inteligente (fixas, recorrentes, variáveis por média)
│   │   ├── conciliacao.py       # Motor 3 camadas (dicionário → fuzzy → palavras-chave)
│   │   └── importacao.py        # Parser OFX/CSV + detecção de formato
│   └── templates/
│       ├── base.html            # Layout: navbar, FAB, modal, dark mode toggle
│       ├── dashboard.html       # Cards resumo + gráfico + calendário + seletor de dias
│       ├── transacoes.html      # Filtros por botões (mês + conta) + lista HTMX
│       ├── categorias.html      # Form inline + tabela
│       ├── contas.html          # Form inline + grid cards
│       ├── importacao.html      # Upload + box explicativo
│       └── partials/            # Fragmentos HTML para HTMX swap
├── tests/
│   ├── conftest.py              # Fixtures: SQLite in-memory + AsyncClient
│   ├── test_api.py              # 40 testes integração HTTP
│   ├── test_schemas.py          # 22 testes validação Pydantic
│   ├── test_models.py           # 17 testes models
│   ├── test_projecao.py         # 45 testes projeção
│   ├── test_conciliacao.py      # 19 testes conciliação
│   └── test_importacao.py       # 21 testes importação
├── alembic/                     # Migrations
├── scripts/
│   └── seed.py                  # 24 categorias iniciais (idempotente)
├── .github/
│   └── copilot-instructions.md  # Convenções de desenvolvimento
├── Dockerfile                   # Multi-stage build (python:3.11-slim)
├── docker-compose.yml           # App + PostgreSQL 16
├── entrypoint.sh                # Wait-for-db + seed + uvicorn
├── requirements.txt
├── alembic.ini
└── .env.example
```

## 📋 Modelo de Dados

- **Contas** — Contas bancárias e carteiras (`nome`, `saldo_inicial`)
- **Categorias** — Classificação com tipo (`Receita`/`Despesa`) e natureza (`Fixa`/`Recorrente`/`Variável`/`Esporádica`)
- **Transações** — Registros financeiros com ciclo de vida (`Projetada` → `Executada`), parcelas opcionais (`parcela_atual`, `total_parcelas`) e `descricao_banco`
- **Dicionário de Conciliação** — Mapeia descrições bancárias para categorias (aprendizado automático)

## 🔄 Ciclo de Vida das Transações

1. **Projetada** → Transação futura baseada em regras (afeta linha pontilhada do gráfico)
2. **Executada** → Transação real confirmada via extrato (valor exato do banco)

## 🔮 Projeção Inteligente

O sistema gera transações virtuais futuras com base na natureza da categoria:

| Natureza | Comportamento na Projeção |
|----------|--------------------------|
| **Fixa** | Repete mensalmente no mesmo dia, indefinidamente |
| **Recorrente** | Projeta parcelas restantes com base em `parcela_atual` / `total_parcelas` |
| **Variável** | Projeta no dia 15 de cada mês futuro usando a **média mensal histórica** da categoria |
| **Esporádica** | **Não projeta** — gastos imprevisíveis/únicos |

O horizonte de projeção é configurável no dashboard (30, 60, 90, 180 dias ou 1 ano).

## 🧠 Motor de Conciliação

Ao importar um extrato, cada linha passa por 3 etapas:

1. **Dicionário Histórico** — Match exato com descrições já mapeadas (100% automático)
2. **Fuzzy Matching** — Busca transações projetadas por data (±3 dias) e valor (±5%)
3. **Palavras-chave** — Compara descrição com nomes de categorias via similaridade de texto

Cada confirmação alimenta o dicionário para automatizar importações futuras! 🎯

## 🏗 Decisões de Arquitetura

- **HTML over the wire** — Jinja2 + HTMX em vez de SPA. Partials retornam fragmentos HTML.
- **CDN para CSS/JS** — Tailwind e Chart.js via CDN, sem build step.
- **Funções `_sync`** — Cada serviço expõe versão síncrona para testes unitários sem banco.
- **Despesas como valores negativos** — Armazenadas como negativos no banco; o form converte automaticamente.
- **Hot-reload com Docker** — Volume `./app:/app/app` + `--reload` reflete mudanças sem rebuild.
- **Entrypoint com wait-for-db** — Socket Python aguarda PostgreSQL antes de seed e uvicorn.
