# Product Requirements Document (PRD) - App de Finanças Pessoais

## 1. Visão Geral e Propósito
Este projeto visa criar uma aplicação web de finanças pessoais focada em previsibilidade e facilidade de inserção de dados. Diferente das soluções de mercado que focam apenas no passado (retrovisor), o diferencial deste app é a **projeção visual do saldo dia a dia no futuro**, cruzando receitas com despesas fixas, recorrentes e a média das variáveis. O sistema busca eliminar o atrito da entrada manual exaustiva através de um motor inteligente de importação e conciliação bancária de extratos (OFX/CSV) com aprendizado contínuo.

## 2. Público-Alvo
* **Uso estritamente individual (Single-player):** O sistema é desenhado para um único usuário final gerenciar seu fluxo de caixa pessoal. Não há necessidade inicial de perfis compartilhados, permissões complexas ou multi-tenancy.

## 3. Escopo de Funcionalidades (Matriz MoSCoW)

### Must Have (MVP)
* **Dashboard Visual Interativo:** Gráfico de projeção diária de saldo (linha sólida para o passado, pontilhada para o futuro) e visão de calendário com alertas (dias negativos ou de alto impacto).
* **Gestão de Transações (CRUD):** Capacidade de inserir manualmente receitas e despesas de forma rápida (modal/atalho).
* **Classificação de Despesas:** Categorização inteligente como *Fixa*, *Recorrente* ou *Variável*.
* **Importação de Extratos:** Suporte para upload de arquivos `.ofx` e `.csv`.
* **Motor de Conciliação Inteligente:** Algoritmo que lê o extrato e sugere o *match* com transações "Projetadas" (baseado em data, valor e palavras-chave).
* **Loop de Aprendizado:** Ao confirmar uma conciliação, o sistema salva a descrição do banco vinculada à despesa para automatizar importações futuras.

### Should Have (Versão 1.1+)
* Importação de dados financeiros via extração de `.pdf`.
* Exportação dos dados consolidados para `.csv`.
* Gráficos secundários de distribuição (ex: pizza/barras de gastos por categoria no mês passado).

### Won't Have (Fora do escopo atual)
* Integração automática direta com APIs de bancos (Open Finance).
* Rateio de contas com múltiplos usuários.

## 4. Arquitetura e Stack Tecnológica

* **Backend:** Python + FastAPI. Escolhido pela alta performance, facilidade na criação de rotas assíncronas e robustez matemática/lógica.
* **Banco de Dados:** PostgreSQL (relacional, ideal para garantir a integridade de dados financeiros).
* **Frontend:** Abordagem *HTML over the wire*. 
  * Templates renderizados via Jinja2.
  * Reatividade e chamadas assíncronas sem recarregar a página usando HTMX.
  * Estilização com Tailwind CSS (ou framework CSS similar) para um design limpo e responsivo sem escrever CSS complexo.
* **Qualidade:** Forte recomendação de criar uma suíte robusta de testes unitários no Python (usando `pytest`), focando especificamente no algoritmo de conciliação e no cálculo de projeção de saldo. 

## 5. Regras de Negócio e Lógica Core

**5.1. Ciclo de Vida da Transação (Status)**
* `Projetada`: Transação futura criada pelo sistema com base nas regras de recorrência ou médias. Afeta a linha pontilhada do gráfico de projeção.
* `Executada` (Realizada): Transação que já ocorreu de fato. Quando um import de extrato dá "match" com uma transação `Projetada`, o status muda para `Executada` e o valor previsto é substituído pelo valor exato (ao centavo) executado no banco.

**5.2. Motor de Conciliação e Aprendizado (*Fuzzy Matching*)**
Ao importar um arquivo, o backend processará cada linha buscando correspondências na seguinte ordem de prioridade:
1. **Dicionário Histórico (Exato):** Checa se a `descricao_banco` já foi mapeada anteriormente para uma despesa específica. Match automático.
2. **Busca Aproximada (Fuzzy):** Busca despesas `Projetadas` em uma janela de tolerância (ex: +/- 3 dias) e margem de valor (ex: valor exato ou margem de 5%).
3. **Palavras-chave (Fallback):** Verifica similaridade de texto entre a descrição do banco e o nome da categoria/despesa.
*Ação:* Ao confirmar a sugestão na UI, o sistema atualiza o status, o valor e alimenta a tabela de "Dicionário Histórico" para o passo 1.

## 6. Modelo de Dados (Rascunho de Entidades Principais)

* **`Contas`**: `id`, `nome` (ex: NuConta, Itaú, Carteira), `saldo_inicial`.
* **`Categorias`**: `id`, `nome`, `tipo` (Receita/Despesa), `natureza` (Fixa, Recorrente, Variável).
* **`Transacoes`**: `id`, `conta_id`, `categoria_id`, `valor_previsto`, `valor_realizado`, `data_vencimento`, `data_pagamento`, `status` (Projetada/Executada), `descricao`.
* **`Dicionario_Conciliacao`**: `id`, `descricao_banco` (string exata que vem no extrato), `categoria_id` (chave estrangeira para vincular automaticamente na próxima vez).

## 7. UI/UX e Visualização

* **Gráfico Principal:** Eixo X (Dias do Mês/Futuro), Eixo Y (Saldo). Linha contínua até o dia atual, pontilhada para o futuro. *Tooltips* interativos ao passar o mouse exibem as composições diárias.
* **Calendário/Grid:** Visão mensal indicando saúde financeira diária. Alertas visuais (vermelho) para dias com previsão de saldo negativo ou alto volume de saídas fixas.
* **Entrada Rápida:** Botão de Ação Flutuante (FAB) global no canto inferior para cadastro ágil de transações não previstas, minimizando cliques.