# Copilot Instructions — Willu

Instruções persistentes para LLMs que trabalham neste workspace.
Este arquivo é lido automaticamente pelo GitHub Copilot como contexto em toda interação.

---

## 📂 Contexto do Projeto

Antes de começar qualquer tarefa, leia os seguintes arquivos para entender o estado atual:

- `.prompts/progresso.md` — Registro de progresso, bugs conhecidos e roadmap.
- `.prompts/prompt-prd.md` — PRD completo do produto.

---

## 🔧 Convenções de Desenvolvimento

### Gerenciamento de Dependências

- **Sempre que instalar uma nova biblioteca** (via `pip install`), **atualize imediatamente o `requirements.txt`** com a versão exata instalada (`lib==X.Y.Z`).
- Para verificar a versão instalada: `pip show <pacote> | grep Version`.
- Dependências de teste/dev ficam no mesmo `requirements.txt` (sem separação por arquivo).
- Após editar `requirements.txt`, valide com `pip install -r requirements.txt` para garantir que não há conflitos.

### Testes

- Seguir o princípio **TDD** — escrever testes primeiro quando possível.
- Testes ficam em `tests/` e usam `pytest` com `pytest-asyncio`.
- Testes unitários usam funções `_sync` dos serviços (sem banco de dados).
- Testes de integração HTTP usam SQLite in-memory via fixtures de `tests/conftest.py`.
- **Sempre rodar `pytest tests/ -v`** após qualquer alteração para validar que nada quebrou.

### Código Python

- Async por padrão nos routers e serviços (FastAPI + SQLAlchemy async).
- Cada serviço expõe uma versão `_sync` pura para testes unitários.
- Models SQLAlchemy em `app/models/`, schemas Pydantic em `app/schemas/`.
- Lógica de negócio em `app/services/`, nunca diretamente nos routers.
- Enums definidos no model correspondente (ex: `StatusTransacao` em `models/transacao.py`).

### Templates e Frontend

- HTML over the wire: Jinja2 + HTMX. Partials retornam fragmentos HTML.
- CSS/JS via CDN (Tailwind, Chart.js, HTMX) — sem build step.
- Partials ficam em `app/templates/partials/`.

### Docker

- Ao alterar `requirements.txt`, o container precisa de rebuild: `docker compose up --build -d`.
- Volume `./app:/app/app` permite hot-reload de código Python e templates.

### Commits e Progresso

- Após concluir uma sessão de trabalho significativa, **atualizar `.prompts/progresso.md`** com:
  - O que foi feito (changelog).
  - Bugs encontrados/corrigidos.
  - Novos débitos técnicos.
  - Atualizar contagem de testes.
