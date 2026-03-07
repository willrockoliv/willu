"""
Testes de integração HTTP para os endpoints FastAPI.
Usa httpx.AsyncClient com SQLite in-memory via fixtures de conftest.py.
"""

import json
import pytest
from datetime import date


# ───────────────────────────── Contas ─────────────────────────────


class TestContasAPI:
    """Testes de integração para endpoints de Contas."""

    @pytest.mark.asyncio
    async def test_listar_contas_vazio(self, client):
        """Página deve carregar mesmo sem contas."""
        response = await client.get("/contas/")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_criar_conta(self, client):
        """POST deve criar conta e retornar lista atualizada."""
        response = await client.post(
            "/contas/",
            data={"nome": "Nubank", "saldo_inicial": "1500.50"},
        )
        assert response.status_code == 200
        assert "Nubank" in response.text

    @pytest.mark.asyncio
    async def test_criar_e_listar_conta(self, client):
        """Conta criada deve aparecer na listagem."""
        await client.post("/contas/", data={"nome": "Itaú", "saldo_inicial": "3000"})
        response = await client.get("/contas/lista")
        assert response.status_code == 200
        assert "Itaú" in response.text

    @pytest.mark.asyncio
    async def test_criar_multiplas_contas(self, client):
        """Múltiplas contas devem aparecer na listagem."""
        await client.post("/contas/", data={"nome": "Nubank", "saldo_inicial": "5000"})
        await client.post("/contas/", data={"nome": "Itaú", "saldo_inicial": "3000"})
        response = await client.get("/contas/lista")
        assert "Nubank" in response.text
        assert "Itaú" in response.text

    @pytest.mark.asyncio
    async def test_deletar_conta(self, client):
        """DELETE deve remover a conta da lista."""
        await client.post("/contas/", data={"nome": "Para Deletar", "saldo_inicial": "0"})
        response = await client.get("/contas/lista")
        assert "Para Deletar" in response.text

        response = await client.delete("/contas/1")
        assert response.status_code == 200
        assert "Para Deletar" not in response.text

    @pytest.mark.asyncio
    async def test_atualizar_conta(self, client):
        """PUT deve atualizar dados da conta."""
        await client.post("/contas/", data={"nome": "Antiga", "saldo_inicial": "100"})
        response = await client.put("/contas/1", data={"nome": "Atualizada"})
        assert response.status_code == 200
        assert "Atualizada" in response.text

    @pytest.mark.asyncio
    async def test_atualizar_conta_inexistente(self, client):
        """PUT em conta inexistente deve retornar 404."""
        response = await client.put("/contas/999", data={"nome": "Fantasma"})
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_deletar_conta_inexistente(self, client):
        """DELETE em conta inexistente não deve dar erro (idempotente)."""
        response = await client.delete("/contas/999")
        assert response.status_code == 200


# ───────────────────────────── Categorias ─────────────────────────────


class TestCategoriasAPI:
    """Testes de integração para endpoints de Categorias."""

    @pytest.mark.asyncio
    async def test_listar_categorias_vazio(self, client):
        response = await client.get("/categorias/")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_criar_categoria_despesa(self, client):
        response = await client.post(
            "/categorias/",
            data={"nome": "Aluguel", "tipo": "Despesa", "natureza": "Fixa"},
        )
        assert response.status_code == 200
        assert "Aluguel" in response.text

    @pytest.mark.asyncio
    async def test_criar_categoria_receita(self, client):
        response = await client.post(
            "/categorias/",
            data={"nome": "Salário", "tipo": "Receita", "natureza": "Fixa"},
        )
        assert response.status_code == 200
        assert "Salário" in response.text

    @pytest.mark.asyncio
    async def test_criar_e_listar_categorias(self, client):
        await client.post(
            "/categorias/",
            data={"nome": "Energia", "tipo": "Despesa", "natureza": "Recorrente"},
        )
        response = await client.get("/categorias/lista")
        assert response.status_code == 200
        assert "Energia" in response.text

    @pytest.mark.asyncio
    async def test_deletar_categoria(self, client):
        await client.post(
            "/categorias/",
            data={"nome": "Temporária", "tipo": "Despesa", "natureza": "Variável"},
        )
        response = await client.get("/categorias/lista")
        assert "Temporária" in response.text

        response = await client.delete("/categorias/1")
        assert response.status_code == 200
        assert "Temporária" not in response.text

    @pytest.mark.asyncio
    async def test_categorias_options(self, client):
        """Endpoint de options deve retornar HTML com <option> tags."""
        await client.post(
            "/categorias/",
            data={"nome": "Alimentação", "tipo": "Despesa", "natureza": "Variável"},
        )
        response = await client.get("/categorias/api/options")
        assert response.status_code == 200
        assert "Alimentação" in response.text
        assert "<option" in response.text

    @pytest.mark.asyncio
    async def test_categorias_options_filtro_tipo(self, client):
        """Options com filtro de tipo deve retornar apenas categorias do tipo."""
        await client.post(
            "/categorias/",
            data={"nome": "Aluguel", "tipo": "Despesa", "natureza": "Fixa"},
        )
        await client.post(
            "/categorias/",
            data={"nome": "Salário", "tipo": "Receita", "natureza": "Fixa"},
        )

        response = await client.get("/categorias/api/options?tipo=Receita")
        assert response.status_code == 200
        assert "Salário" in response.text
        assert "Aluguel" not in response.text


# ───────────────────────────── Transações ─────────────────────────────


class TestTransacoesAPI:
    """Testes de integração para endpoints de Transações."""

    async def _criar_conta_e_categoria(self, client):
        """Helper para setup comum de conta + categoria."""
        await client.post("/contas/", data={"nome": "Nubank", "saldo_inicial": "5000"})
        await client.post(
            "/categorias/",
            data={"nome": "Aluguel", "tipo": "Despesa", "natureza": "Fixa"},
        )

    @pytest.mark.asyncio
    async def test_listar_transacoes_vazio(self, client):
        await self._criar_conta_e_categoria(client)
        response = await client.get("/transacoes/")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_criar_transacao_despesa(self, client):
        """Criar despesa deve converter valor para negativo."""
        await self._criar_conta_e_categoria(client)
        hoje = date.today()
        response = await client.post(
            "/transacoes/",
            data={
                "conta_id": "1",
                "categoria_id": "1",
                "valor_previsto": "1500",
                "tipo_valor": "despesa",
                "data_vencimento": hoje.isoformat(),
                "descricao": "Aluguel Março",
                "status": "Projetada",
            },
        )
        assert response.status_code == 200
        assert "✅" in response.text

    @pytest.mark.asyncio
    async def test_criar_transacao_receita(self, client):
        await self._criar_conta_e_categoria(client)
        hoje = date.today()
        response = await client.post(
            "/transacoes/",
            data={
                "conta_id": "1",
                "valor_previsto": "5000",
                "tipo_valor": "receita",
                "data_vencimento": hoje.isoformat(),
                "descricao": "Salário",
                "status": "Projetada",
            },
        )
        assert response.status_code == 200
        assert "✅" in response.text

    @pytest.mark.asyncio
    async def test_form_nova_transacao(self, client):
        """GET /transacoes/form deve retornar formulário modal."""
        await self._criar_conta_e_categoria(client)
        response = await client.get("/transacoes/form")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_form_editar_transacao(self, client):
        """GET /transacoes/form/{id} deve retornar formulário preenchido."""
        await self._criar_conta_e_categoria(client)
        hoje = date.today()
        await client.post(
            "/transacoes/",
            data={
                "conta_id": "1", "categoria_id": "1", "valor_previsto": "100",
                "tipo_valor": "despesa", "data_vencimento": hoje.isoformat(),
                "descricao": "Para Editar", "status": "Projetada",
            },
        )
        response = await client.get("/transacoes/form/1")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_deletar_transacao(self, client):
        await self._criar_conta_e_categoria(client)
        hoje = date.today()
        await client.post(
            "/transacoes/",
            data={
                "conta_id": "1", "valor_previsto": "100", "tipo_valor": "despesa",
                "data_vencimento": hoje.isoformat(), "descricao": "Para Deletar",
                "status": "Projetada",
            },
        )
        response = await client.delete("/transacoes/1")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_atualizar_transacao(self, client):
        await self._criar_conta_e_categoria(client)
        hoje = date.today()
        await client.post(
            "/transacoes/",
            data={
                "conta_id": "1", "categoria_id": "1", "valor_previsto": "100",
                "tipo_valor": "despesa", "data_vencimento": hoje.isoformat(),
                "descricao": "Original", "status": "Projetada",
            },
        )
        response = await client.put(
            "/transacoes/1",
            data={"descricao": "Atualizada"},
        )
        assert response.status_code == 200
        assert "✅" in response.text

    @pytest.mark.asyncio
    async def test_atualizar_transacao_inexistente(self, client):
        response = await client.put(
            "/transacoes/999",
            data={"descricao": "Fantasma"},
        )
        assert response.status_code == 404


# ───────────────────────────── Dashboard ─────────────────────────────


class TestDashboardAPI:
    """Testes de integração para o Dashboard."""

    @pytest.mark.asyncio
    async def test_dashboard_sem_contas(self, client):
        """Dashboard deve renderizar mesmo sem dados."""
        response = await client.get("/")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_dashboard_com_conta(self, client):
        """Dashboard com conta deve mostrar gráfico/projeção."""
        await client.post("/contas/", data={"nome": "Nubank", "saldo_inicial": "5000"})
        response = await client.get("/")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_dashboard_seleciona_conta(self, client):
        """Dashboard com conta_id específica."""
        await client.post("/contas/", data={"nome": "Nubank", "saldo_inicial": "5000"})
        response = await client.get("/?conta_id=1")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_api_projecao(self, client):
        """API de projeção deve retornar partial do gráfico."""
        await client.post("/contas/", data={"nome": "Nubank", "saldo_inicial": "5000"})
        response = await client.get("/api/projecao?conta_id=1")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_api_calendario(self, client):
        """API de calendário deve retornar partial com grid."""
        await client.post("/contas/", data={"nome": "Nubank", "saldo_inicial": "5000"})
        response = await client.get("/api/calendario?conta_id=1&ano=2026&mes=3")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_api_projecao_com_transacoes(self, client):
        """Projeção deve refletir transações existentes."""
        await client.post("/contas/", data={"nome": "Nubank", "saldo_inicial": "5000"})
        await client.post(
            "/categorias/",
            data={"nome": "Aluguel", "tipo": "Despesa", "natureza": "Fixa"},
        )
        hoje = date.today()
        await client.post(
            "/transacoes/",
            data={
                "conta_id": "1", "categoria_id": "1", "valor_previsto": "1500",
                "tipo_valor": "despesa", "data_vencimento": hoje.isoformat(),
                "descricao": "Aluguel", "status": "Projetada",
            },
        )
        response = await client.get("/api/projecao?conta_id=1")
        assert response.status_code == 200


# ───────────────────────────── Importação ─────────────────────────────


class TestImportacaoAPI:
    """Testes de integração para endpoints de Importação."""

    @pytest.mark.asyncio
    async def test_pagina_importacao(self, client):
        """Página de importação deve carregar."""
        response = await client.get("/importacao/")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_upload_csv(self, client):
        """Upload de CSV deve retornar sugestões de conciliação."""
        await client.post("/contas/", data={"nome": "Nubank", "saldo_inicial": "5000"})

        csv_content = (
            "Data;Descrição;Extra;Valor\n"
            "05-03-2026;PGTO ALUGUEL;X;-1500,00\n"
            "06-03-2026;PIX RECEBIDO;X;3000,50\n"
        ).encode("utf-8")

        response = await client.post(
            "/importacao/upload",
            data={"conta_id": "1"},
            files={"arquivo": ("extrato.csv", csv_content, "text/csv")},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_upload_csv_com_conciliacao(self, client):
        """Upload de CSV com transação existente deve sugerir match."""
        await client.post("/contas/", data={"nome": "Nubank", "saldo_inicial": "5000"})
        await client.post(
            "/categorias/",
            data={"nome": "Aluguel", "tipo": "Despesa", "natureza": "Fixa"},
        )
        await client.post(
            "/transacoes/",
            data={
                "conta_id": "1", "categoria_id": "1", "valor_previsto": "1500",
                "tipo_valor": "despesa", "data_vencimento": "2026-03-05",
                "descricao": "Aluguel", "status": "Projetada",
            },
        )

        csv_content = (
            "Data;Descrição;Extra;Valor\n"
            "05-03-2026;PGTO ALUGUEL;X;-1500,00\n"
        ).encode("utf-8")

        response = await client.post(
            "/importacao/upload",
            data={"conta_id": "1"},
            files={"arquivo": ("extrato.csv", csv_content, "text/csv")},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_confirmar_conciliacao(self, client):
        """Confirmar conciliação deve criar transação executada."""
        await client.post("/contas/", data={"nome": "Nubank", "saldo_inicial": "5000"})
        await client.post(
            "/categorias/",
            data={"nome": "Aluguel", "tipo": "Despesa", "natureza": "Fixa"},
        )

        response = await client.post(
            "/importacao/confirmar",
            data={
                "data": "2026-03-05",
                "descricao_banco": "PGTO ALUGUEL",
                "valor": "-1500.0",
                "categoria_id": "1",
                "descricao": "Aluguel Apartamento",
                "conta_id": "1",
                "salvar_dicionario": "on",
            },
        )
        assert response.status_code == 200
        assert "✅" in response.text

    @pytest.mark.asyncio
    async def test_confirmar_todas(self, client):
        """Confirmar todas deve processar múltiplas conciliações."""
        await client.post("/contas/", data={"nome": "Nubank", "saldo_inicial": "5000"})
        await client.post(
            "/categorias/",
            data={"nome": "Aluguel", "tipo": "Despesa", "natureza": "Fixa"},
        )

        dados = [
            {
                "data": "2026-03-05",
                "descricao_banco": "PGTO ALUGUEL",
                "valor": "-1500.0",
                "categoria_id": "1",
                "descricao": "Aluguel",
                "conta_id": "1",
            },
            {
                "data": "2026-03-06",
                "descricao_banco": "PIX RECEBIDO",
                "valor": "3000.50",
                "categoria_id": "1",
                "descricao": "PIX",
                "conta_id": "1",
            },
        ]

        response = await client.post(
            "/importacao/confirmar-todas",
            data={"dados": json.dumps(dados)},
        )
        assert response.status_code == 200
        assert "2" in response.text  # "2 transações conciliadas"

    @pytest.mark.asyncio
    async def test_confirmar_todas_sem_dados(self, client):
        """Confirmar todas sem dados deve retornar erro."""
        response = await client.post(
            "/importacao/confirmar-todas",
            data={"dados": ""},
        )
        assert response.status_code == 200
        # Deve conter mensagem de erro
