# 💰 Willu - Finanças Pessoais

Aplicação web de finanças pessoais com foco em **projeção de saldo futuro** e **conciliação inteligente de extratos bancários**.

## ✨ Funcionalidades

- 📊 **Dashboard Visual** — Gráfico de projeção diária de saldo (linha sólida para passado, pontilhada para futuro)
- 📅 **Calendário Financeiro** — Visão mensal com alertas para dias negativos ou de alto impacto
- ➕ **Entrada Rápida** — FAB (Floating Action Button) para cadastro ágil de transações
- 📂 **Importação de Extratos** — Suporte para arquivos `.ofx` e `.csv`
- 🧠 **Conciliação Inteligente** — Motor de matching: Dicionário → Fuzzy → Palavras-chave
- 🔄 **Aprendizado Contínuo** — Cada confirmação alimenta o dicionário para automatizar futuras importações

## 🛠 Stack Tecnológica

| Componente | Tecnologia |
|-----------|-----------|
| Backend | Python + FastAPI |
| Banco de Dados | PostgreSQL |
| ORM | SQLAlchemy (async) |
| Migrations | Alembic |
| Frontend | Jinja2 + HTMX + Tailwind CSS |
| Gráficos | Chart.js |
| Testes | pytest |

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

#### 5. Rodar a aplicação

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Acesse: **http://localhost:8000**

## 🧪 Testes

```bash
pytest tests/ -v
```

Os testes cobrem:
- **Projeção de Saldo** — Cálculos diários, acumulação, saldo negativo, arredondamento
- **Motor de Conciliação** — Dicionário, fuzzy matching, palavras-chave, prioridades
- **Importação** — Parsing de CSV, detecção de formato

## 📁 Estrutura do Projeto

```
willu/
├── app/
│   ├── main.py              # Entrypoint FastAPI
│   ├── config.py             # Configurações (env vars)
│   ├── database.py           # Engine SQLAlchemy async
│   ├── models/               # Modelos ORM
│   │   ├── conta.py
│   │   ├── categoria.py
│   │   ├── transacao.py
│   │   └── dicionario_conciliacao.py
│   ├── schemas/              # Schemas Pydantic
│   ├── routers/              # Rotas FastAPI (controllers)
│   │   ├── dashboard.py
│   │   ├── contas.py
│   │   ├── categorias.py
│   │   ├── transacoes.py
│   │   └── importacao.py
│   ├── services/             # Lógica de negócio
│   │   ├── projecao.py       # Cálculo de projeção de saldo
│   │   ├── conciliacao.py    # Motor de conciliação inteligente
│   │   └── importacao.py     # Parser OFX/CSV
│   └── templates/            # Templates Jinja2 + HTMX
│       ├── base.html
│       ├── dashboard.html
│       ├── transacoes.html
│       ├── categorias.html
│       ├── contas.html
│       ├── importacao.html
│       └── partials/         # Fragmentos HTMX
├── tests/                    # Testes pytest
├── alembic/                  # Migrations
├── scripts/
│   └── seed.py               # Dados iniciais
├── Dockerfile                # Multi-stage build (python:3.11-slim)
├── docker-compose.yml        # App + PostgreSQL 16
├── entrypoint.sh             # Wait-for-db + seed + uvicorn
├── .dockerignore
├── requirements.txt
├── alembic.ini
└── .env.example
```

## 📋 Modelo de Dados

- **Contas** — Contas bancárias e carteiras (nome, saldo_inicial)
- **Categorias** — Classificação com tipo (Receita/Despesa) e natureza (Fixa/Recorrente/Variável)
- **Transações** — Registros financeiros com ciclo de vida (Projetada → Executada)
- **Dicionário de Conciliação** — Mapeia descrições bancárias para categorias (aprendizado)

## 🔄 Ciclo de Vida das Transações

1. **Projetada** → Transação futura baseada em regras (afeta linha pontilhada do gráfico)
2. **Executada** → Transação real confirmada via extrato (valor exato do banco)

## 🧠 Motor de Conciliação

Ao importar um extrato, cada linha passa por 3 etapas:

1. **Dicionário Histórico** — Match exato com descrições já mapeadas (100% automático)
2. **Fuzzy Matching** — Busca transações projetadas por data (±3 dias) e valor (±5%)
3. **Palavras-chave** — Compara descrição com nomes de categorias via similaridade de texto

Cada confirmação alimenta o dicionário para automatizar importações futuras! 🎯
