"""
Testes unitários para o serviço de projeção de saldo.
Foca na lógica de cálculo de saldo dia a dia,
incluindo geração de transações virtuais para despesas fixas, recorrentes e variáveis.
"""

import pytest
from datetime import date, timedelta
from app.services.projecao import (
    calcular_projecao_sync,
    _add_months,
    _gerar_virtuais,
    _calcular_media_mensal,
)


class TestProjecaoSaldo:
    """Testes para cálculo de projeção de saldo."""

    def test_projecao_sem_transacoes(self):
        """Saldo deve se manter constante sem transações."""
        resultado = calcular_projecao_sync(
            saldo_inicial=1000.0,
            transacoes=[],
            data_inicio=date(2026, 3, 1),
            data_fim=date(2026, 3, 5),
        )
        assert len(resultado) == 5
        for dia in resultado:
            assert dia["saldo"] == 1000.0

    def test_projecao_com_despesa(self):
        """Saldo deve diminuir no dia da despesa."""
        transacoes = [
            {"data": date(2026, 3, 3), "valor": -500.0, "status": "Projetada", "descricao": "Aluguel"},
        ]
        resultado = calcular_projecao_sync(
            saldo_inicial=2000.0,
            transacoes=transacoes,
            data_inicio=date(2026, 3, 1),
            data_fim=date(2026, 3, 5),
        )
        # Dia 1-2: 2000, Dia 3: 1500, Dia 4-5: 1500
        assert resultado[0]["saldo"] == 2000.0
        assert resultado[1]["saldo"] == 2000.0
        assert resultado[2]["saldo"] == 1500.0
        assert resultado[3]["saldo"] == 1500.0
        assert resultado[4]["saldo"] == 1500.0

    def test_projecao_com_receita(self):
        """Saldo deve aumentar no dia da receita."""
        transacoes = [
            {"data": date(2026, 3, 5), "valor": 5000.0, "status": "Projetada", "descricao": "Salário"},
        ]
        resultado = calcular_projecao_sync(
            saldo_inicial=100.0,
            transacoes=transacoes,
            data_inicio=date(2026, 3, 1),
            data_fim=date(2026, 3, 7),
        )
        assert resultado[0]["saldo"] == 100.0
        assert resultado[4]["saldo"] == 5100.0
        assert resultado[5]["saldo"] == 5100.0

    def test_projecao_multiplas_transacoes_mesmo_dia(self):
        """Múltiplas transações no mesmo dia devem ser acumuladas."""
        transacoes = [
            {"data": date(2026, 3, 2), "valor": -100.0, "status": "Executada", "descricao": "Supermercado"},
            {"data": date(2026, 3, 2), "valor": -50.0, "status": "Executada", "descricao": "Farmácia"},
            {"data": date(2026, 3, 2), "valor": 200.0, "status": "Executada", "descricao": "Reembolso"},
        ]
        resultado = calcular_projecao_sync(
            saldo_inicial=1000.0,
            transacoes=transacoes,
            data_inicio=date(2026, 3, 1),
            data_fim=date(2026, 3, 3),
        )
        # Dia 1: 1000, Dia 2: 1000 + (-100 - 50 + 200) = 1050, Dia 3: 1050
        assert resultado[0]["saldo"] == 1000.0
        assert resultado[1]["saldo"] == 1050.0
        assert resultado[2]["saldo"] == 1050.0

    def test_projecao_saldo_negativo(self):
        """Deve permitir e exibir saldo negativo."""
        transacoes = [
            {"data": date(2026, 3, 1), "valor": -1500.0, "status": "Projetada", "descricao": "Aluguel"},
        ]
        resultado = calcular_projecao_sync(
            saldo_inicial=1000.0,
            transacoes=transacoes,
            data_inicio=date(2026, 3, 1),
            data_fim=date(2026, 3, 2),
        )
        assert resultado[0]["saldo"] == -500.0

    def test_projecao_tipo_campo(self):
        """Deve marcar dias passados como 'real' e futuros como 'projetado'."""
        hoje = date.today()
        ontem = hoje - timedelta(days=1)
        amanha = hoje + timedelta(days=1)

        resultado = calcular_projecao_sync(
            saldo_inicial=500.0,
            transacoes=[],
            data_inicio=ontem,
            data_fim=amanha,
        )
        assert resultado[0]["tipo"] == "real"      # ontem
        assert resultado[1]["tipo"] == "real"      # hoje
        assert resultado[2]["tipo"] == "projetado"  # amanhã

    def test_projecao_movimentacao_diaria(self):
        """O campo movimentacao deve refletir o total de movimentação do dia."""
        transacoes = [
            {"data": date(2026, 3, 1), "valor": -300.0, "status": "Projetada", "descricao": "Conta"},
            {"data": date(2026, 3, 1), "valor": -200.0, "status": "Projetada", "descricao": "Outra"},
        ]
        resultado = calcular_projecao_sync(
            saldo_inicial=1000.0,
            transacoes=transacoes,
            data_inicio=date(2026, 3, 1),
            data_fim=date(2026, 3, 1),
        )
        assert resultado[0]["movimentacao"] == -500.0
        assert resultado[0]["saldo"] == 500.0

    def test_projecao_acumula_antes_do_periodo(self):
        """Transações antes do período devem afetar o saldo inicial."""
        transacoes = [
            {"data": date(2026, 2, 15), "valor": -500.0, "status": "Executada", "descricao": "Anterior"},
        ]
        resultado = calcular_projecao_sync(
            saldo_inicial=2000.0,
            transacoes=transacoes,
            data_inicio=date(2026, 3, 1),
            data_fim=date(2026, 3, 1),
        )
        assert resultado[0]["saldo"] == 1500.0

    def test_projecao_arredondamento(self):
        """Valores devem ser arredondados para 2 casas decimais."""
        transacoes = [
            {"data": date(2026, 3, 1), "valor": -33.33, "status": "Projetada", "descricao": "A"},
            {"data": date(2026, 3, 1), "valor": -33.33, "status": "Projetada", "descricao": "B"},
            {"data": date(2026, 3, 1), "valor": -33.34, "status": "Projetada", "descricao": "C"},
        ]
        resultado = calcular_projecao_sync(
            saldo_inicial=100.0,
            transacoes=transacoes,
            data_inicio=date(2026, 3, 1),
            data_fim=date(2026, 3, 1),
        )
        assert resultado[0]["saldo"] == 0.0


class TestProjecaoEdgeCases:
    """Testes de edge cases para projeção de saldo."""

    def test_projecao_periodo_unico_dia(self):
        """Período de 1 dia deve retornar exatamente 1 registro."""
        resultado = calcular_projecao_sync(
            saldo_inicial=500.0,
            transacoes=[],
            data_inicio=date(2026, 3, 15),
            data_fim=date(2026, 3, 15),
        )
        assert len(resultado) == 1
        assert resultado[0]["saldo"] == 500.0
        assert resultado[0]["data"] == "2026-03-15"

    def test_projecao_saldo_zero(self):
        """Saldo zero é válido e deve ser exibido."""
        transacoes = [
            {"data": date(2026, 3, 1), "valor": -1000.0, "status": "Projetada", "descricao": "Tudo"},
        ]
        resultado = calcular_projecao_sync(
            saldo_inicial=1000.0,
            transacoes=transacoes,
            data_inicio=date(2026, 3, 1),
            data_fim=date(2026, 3, 1),
        )
        assert resultado[0]["saldo"] == 0.0
        assert resultado[0]["movimentacao"] == -1000.0

    def test_projecao_transacoes_antes_e_durante_periodo(self):
        """Mix de transações antes e durante o período."""
        transacoes = [
            {"data": date(2026, 2, 1), "valor": -200.0, "status": "Executada", "descricao": "Antes 1"},
            {"data": date(2026, 2, 15), "valor": -300.0, "status": "Executada", "descricao": "Antes 2"},
            {"data": date(2026, 3, 1), "valor": -100.0, "status": "Projetada", "descricao": "Durante"},
        ]
        resultado = calcular_projecao_sync(
            saldo_inicial=1000.0,
            transacoes=transacoes,
            data_inicio=date(2026, 3, 1),
            data_fim=date(2026, 3, 2),
        )
        # 1000 - 200 - 300 = 500 (antes do período)
        # 500 - 100 = 400 (dia 1)
        assert resultado[0]["saldo"] == 400.0
        assert resultado[1]["saldo"] == 400.0

    def test_projecao_valores_grandes(self):
        """Deve lidar com valores altos sem problemas de precisão."""
        transacoes = [
            {"data": date(2026, 3, 1), "valor": 1000000.00, "status": "Projetada", "descricao": "Prêmio"},
        ]
        resultado = calcular_projecao_sync(
            saldo_inicial=500000.50,
            transacoes=transacoes,
            data_inicio=date(2026, 3, 1),
            data_fim=date(2026, 3, 1),
        )
        assert resultado[0]["saldo"] == 1500000.50

    def test_projecao_saldo_inicial_negativo(self):
        """Conta com saldo inicial negativo (cheque especial)."""
        resultado = calcular_projecao_sync(
            saldo_inicial=-500.0,
            transacoes=[],
            data_inicio=date(2026, 3, 1),
            data_fim=date(2026, 3, 3),
        )
        assert resultado[0]["saldo"] == -500.0
        assert resultado[1]["saldo"] == -500.0
        assert resultado[2]["saldo"] == -500.0

    def test_projecao_movimentacao_zero_dia_sem_transacoes(self):
        """Dias sem transações devem ter movimentação zero."""
        transacoes = [
            {"data": date(2026, 3, 2), "valor": -100.0, "status": "Projetada", "descricao": "Dia 2"},
        ]
        resultado = calcular_projecao_sync(
            saldo_inicial=1000.0,
            transacoes=transacoes,
            data_inicio=date(2026, 3, 1),
            data_fim=date(2026, 3, 3),
        )
        assert resultado[0]["movimentacao"] == 0.0
        assert resultado[1]["movimentacao"] == -100.0
        assert resultado[2]["movimentacao"] == 0.0


class TestAddMonths:
    """Testes para a função auxiliar _add_months."""

    def test_add_months_basico(self):
        """Adicionar meses a uma data normal."""
        assert _add_months(date(2026, 1, 15), 1) == date(2026, 2, 15)
        assert _add_months(date(2026, 1, 15), 3) == date(2026, 4, 15)

    def test_add_months_fim_mes_curto(self):
        """Dia 31 de janeiro + 1 mês → dia 28 de fevereiro."""
        assert _add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)

    def test_add_months_ano_bissexto(self):
        """Dia 29 de janeiro → fevereiro em ano bissexto."""
        assert _add_months(date(2024, 1, 29), 1) == date(2024, 2, 29)
        assert _add_months(date(2025, 1, 29), 1) == date(2025, 2, 28)

    def test_add_months_virada_ano(self):
        """Dezembro + 1 mês → janeiro do próximo ano."""
        assert _add_months(date(2026, 12, 15), 1) == date(2027, 1, 15)
        assert _add_months(date(2026, 12, 31), 2) == date(2027, 2, 28)

    def test_add_months_multiplos(self):
        """Adicionar muitos meses de uma vez."""
        assert _add_months(date(2026, 1, 1), 12) == date(2027, 1, 1)
        assert _add_months(date(2026, 3, 15), 24) == date(2028, 3, 15)


class TestProjecaoVirtuais:
    """Testes para geração de transações virtuais na projeção."""

    def test_despesa_fixa_projeta_meses_futuros(self):
        """Despesa fixa gera projeções mensais no futuro."""
        hoje = date(2026, 3, 7)
        transacoes = [
            {
                "data": date(2026, 3, 5),
                "valor": -1500.0,
                "status": "Executada",
                "descricao": "Aluguel",
                "categoria_id": 1,
                "natureza": "Fixa",
            },
        ]
        resultado = calcular_projecao_sync(
            saldo_inicial=10000.0,
            transacoes=transacoes,
            data_inicio=date(2026, 3, 1),
            data_fim=date(2026, 6, 30),
            hoje=hoje,
        )
        # Março: real no dia 5 (-1500). Virtuais: abril, maio, junho no dia 5.
        movs = {p["data"]: p["movimentacao"] for p in resultado if p["movimentacao"] != 0}
        assert movs["2026-03-05"] == -1500.0
        assert movs["2026-04-05"] == -1500.0
        assert movs["2026-05-05"] == -1500.0
        assert movs["2026-06-05"] == -1500.0

        # Saldo final: 10000 - 1500*4 = 4000
        assert resultado[-1]["saldo"] == 4000.0

    def test_despesa_recorrente_projeta_parcelas(self):
        """Despesa recorrente projeta parcelas restantes."""
        hoje = date(2026, 3, 7)
        transacoes = [
            {
                "data": date(2026, 3, 10),
                "valor": -300.0,
                "status": "Projetada",
                "descricao": "Notebook",
                "categoria_id": 2,
                "natureza": "Recorrente",
                "parcela_atual": 3,
                "total_parcelas": 6,
            },
        ]
        resultado = calcular_projecao_sync(
            saldo_inicial=5000.0,
            transacoes=transacoes,
            data_inicio=date(2026, 3, 1),
            data_fim=date(2026, 9, 30),
            hoje=hoje,
        )
        # Parcela 3 em março (real), parcelas 4,5,6 virtuais em abril, maio, junho
        movs = {p["data"]: p["movimentacao"] for p in resultado if p["movimentacao"] != 0}
        assert movs["2026-03-10"] == -300.0   # parcela 3 (real)
        assert movs["2026-04-10"] == -300.0   # parcela 4 (virtual)
        assert movs["2026-05-10"] == -300.0   # parcela 5
        assert movs["2026-06-10"] == -300.0   # parcela 6
        # Não deve haver parcelas em julho (total é 6)
        assert "2026-07-10" not in movs

        # Saldo: 5000 - 300*4 = 3800
        ultimo_dia = resultado[-1]
        assert ultimo_dia["saldo"] == 3800.0

    def test_despesa_variavel_projeta_media(self):
        """Despesa variável projeta média mensal da categoria para meses futuros."""
        hoje = date(2026, 3, 7)
        transacoes = [
            # Janeiro: -150 e -250 = -400
            {
                "data": date(2026, 1, 5),
                "valor": -150.0,
                "status": "Executada",
                "descricao": "Supermercado",
                "categoria_id": 3,
                "natureza": "Variável",
            },
            {
                "data": date(2026, 1, 20),
                "valor": -250.0,
                "status": "Executada",
                "descricao": "Supermercado",
                "categoria_id": 3,
                "natureza": "Variável",
            },
            # Fevereiro: -600
            {
                "data": date(2026, 2, 10),
                "valor": -600.0,
                "status": "Executada",
                "descricao": "Supermercado",
                "categoria_id": 3,
                "natureza": "Variável",
            },
        ]
        resultado = calcular_projecao_sync(
            saldo_inicial=5000.0,
            transacoes=transacoes,
            data_inicio=date(2026, 3, 1),
            data_fim=date(2026, 5, 31),
            hoje=hoje,
        )
        # Média mensal = (-400 + -600) / 2 = -500
        # Projeção no dia 15 de abril e maio (março tem mês incompleto, mas
        # a média é calculada sobre jan e fev apenas)
        movs = {p["data"]: p["movimentacao"] for p in resultado if p["movimentacao"] != 0}
        assert movs.get("2026-04-15") == -500.0
        assert movs.get("2026-05-15") == -500.0

    def test_dedup_nao_duplica_mes_existente(self):
        """Não gera virtual para mês que já possui transação real."""
        hoje = date(2026, 3, 7)
        transacoes = [
            {
                "data": date(2026, 3, 5),
                "valor": -1500.0,
                "status": "Executada",
                "descricao": "Aluguel",
                "categoria_id": 1,
                "natureza": "Fixa",
            },
            {
                "data": date(2026, 4, 5),
                "valor": -1500.0,
                "status": "Projetada",
                "descricao": "Aluguel",
                "categoria_id": 1,
                "natureza": "Fixa",
            },
        ]
        resultado = calcular_projecao_sync(
            saldo_inicial=10000.0,
            transacoes=transacoes,
            data_inicio=date(2026, 3, 1),
            data_fim=date(2026, 5, 31),
            hoje=hoje,
        )
        # Março: real. Abril: real (já existe). Maio: virtual.
        movs = {p["data"]: p["movimentacao"] for p in resultado if p["movimentacao"] != 0}
        assert movs["2026-03-05"] == -1500.0
        assert movs["2026-04-05"] == -1500.0
        assert movs["2026-05-05"] == -1500.0

        # Saldo: 10000 - 1500*3 = 5500
        assert resultado[-1]["saldo"] == 5500.0

    def test_sem_categoria_nao_projeta(self):
        """Transação sem categoria_id não gera projeções."""
        hoje = date(2026, 3, 7)
        transacoes = [
            {
                "data": date(2026, 3, 5),
                "valor": -500.0,
                "status": "Executada",
                "descricao": "Algo",
            },
        ]
        resultado = calcular_projecao_sync(
            saldo_inicial=5000.0,
            transacoes=transacoes,
            data_inicio=date(2026, 3, 1),
            data_fim=date(2026, 6, 30),
            hoje=hoje,
        )
        movs = [p for p in resultado if p["movimentacao"] != 0]
        assert len(movs) == 1
        assert resultado[-1]["saldo"] == 4500.0

    def test_recorrente_sem_parcelas_nao_projeta(self):
        """Recorrente sem parcela_atual/total_parcelas não gera virtuais."""
        hoje = date(2026, 3, 7)
        transacoes = [
            {
                "data": date(2026, 3, 10),
                "valor": -200.0,
                "status": "Projetada",
                "descricao": "Assinatura",
                "categoria_id": 2,
                "natureza": "Recorrente",
            },
        ]
        resultado = calcular_projecao_sync(
            saldo_inicial=5000.0,
            transacoes=transacoes,
            data_inicio=date(2026, 3, 1),
            data_fim=date(2026, 6, 30),
            hoje=hoje,
        )
        movs = [p for p in resultado if p["movimentacao"] != 0]
        assert len(movs) == 1

    def test_recorrente_ultima_parcela_nao_projeta(self):
        """Recorrente com parcela_atual == total_parcelas não gera mais virtuais."""
        hoje = date(2026, 3, 7)
        transacoes = [
            {
                "data": date(2026, 3, 10),
                "valor": -300.0,
                "status": "Projetada",
                "descricao": "Notebook",
                "categoria_id": 2,
                "natureza": "Recorrente",
                "parcela_atual": 12,
                "total_parcelas": 12,
            },
        ]
        resultado = calcular_projecao_sync(
            saldo_inicial=5000.0,
            transacoes=transacoes,
            data_inicio=date(2026, 3, 1),
            data_fim=date(2026, 6, 30),
            hoje=hoje,
        )
        movs = [p for p in resultado if p["movimentacao"] != 0]
        assert len(movs) == 1  # só a parcela 12, nenhuma virtual

    def test_fixa_ajusta_dia_mes_curto(self):
        """Despesa fixa no dia 31 ajusta para meses mais curtos."""
        hoje = date(2026, 1, 15)
        transacoes = [
            {
                "data": date(2026, 1, 31),
                "valor": -500.0,
                "status": "Executada",
                "descricao": "Fatura",
                "categoria_id": 1,
                "natureza": "Fixa",
            },
        ]
        resultado = calcular_projecao_sync(
            saldo_inicial=5000.0,
            transacoes=transacoes,
            data_inicio=date(2026, 1, 1),
            data_fim=date(2026, 4, 30),
            hoje=hoje,
        )
        movs = {p["data"]: p["movimentacao"] for p in resultado if p["movimentacao"] != 0}
        assert movs["2026-01-31"] == -500.0   # real
        assert movs["2026-02-28"] == -500.0   # virtual (fev tem 28 dias)
        assert movs["2026-03-31"] == -500.0   # virtual
        assert movs.get("2026-04-30") == -500.0  # virtual (abr tem 30 dias)

    def test_multiplas_fixas_diferentes_categorias(self):
        """Múltiplas despesas fixas de categorias distintas projetam independentemente."""
        hoje = date(2026, 3, 7)
        transacoes = [
            {
                "data": date(2026, 3, 5),
                "valor": -1500.0,
                "status": "Executada",
                "descricao": "Aluguel",
                "categoria_id": 1,
                "natureza": "Fixa",
            },
            {
                "data": date(2026, 3, 10),
                "valor": -200.0,
                "status": "Executada",
                "descricao": "Internet",
                "categoria_id": 4,
                "natureza": "Fixa",
            },
        ]
        resultado = calcular_projecao_sync(
            saldo_inicial=10000.0,
            transacoes=transacoes,
            data_inicio=date(2026, 3, 1),
            data_fim=date(2026, 5, 31),
            hoje=hoje,
        )
        movs = {p["data"]: p["movimentacao"] for p in resultado if p["movimentacao"] != 0}
        # Março: aluguel + internet reais
        assert movs["2026-03-05"] == -1500.0
        assert movs["2026-03-10"] == -200.0
        # Abril e maio: projeções de ambas
        assert movs["2026-04-05"] == -1500.0
        assert movs["2026-04-10"] == -200.0
        assert movs["2026-05-05"] == -1500.0
        assert movs["2026-05-10"] == -200.0

        # Saldo: 10000 - (1500+200)*3 = 10000 - 5100 = 4900
        assert resultado[-1]["saldo"] == 4900.0

    def test_receita_fixa_projeta_positivo(self):
        """Receita fixa (valor positivo) projeta corretamente."""
        hoje = date(2026, 3, 7)
        transacoes = [
            {
                "data": date(2026, 3, 5),
                "valor": 5000.0,
                "status": "Executada",
                "descricao": "Salário",
                "categoria_id": 10,
                "natureza": "Fixa",
            },
        ]
        resultado = calcular_projecao_sync(
            saldo_inicial=1000.0,
            transacoes=transacoes,
            data_inicio=date(2026, 3, 1),
            data_fim=date(2026, 5, 31),
            hoje=hoje,
        )
        movs = {p["data"]: p["movimentacao"] for p in resultado if p["movimentacao"] != 0}
        assert movs["2026-03-05"] == 5000.0
        assert movs["2026-04-05"] == 5000.0
        assert movs["2026-05-05"] == 5000.0

    def test_gerar_virtuais_isolado(self):
        """Testa _gerar_virtuais diretamente."""
        hoje = date(2026, 3, 7)
        transacoes = [
            {
                "data": date(2026, 3, 5),
                "valor": -1500.0,
                "descricao": "Aluguel",
                "categoria_id": 1,
                "natureza": "Fixa",
            },
        ]
        virtuais = _gerar_virtuais(transacoes, date(2026, 5, 31), hoje=hoje)
        assert len(virtuais) == 2  # abril e maio
        assert all(v["virtual"] is True for v in virtuais)
        assert virtuais[0]["data"] == date(2026, 4, 5)
        assert virtuais[1]["data"] == date(2026, 5, 5)
        assert all(v["valor"] == -1500.0 for v in virtuais)
        assert "projeção" in virtuais[0]["descricao"]

    def test_gerar_virtuais_recorrente_com_descricao_parcela(self):
        """Virtuais recorrentes devem ter descrição com número da parcela."""
        hoje = date(2026, 3, 7)
        transacoes = [
            {
                "data": date(2026, 3, 10),
                "valor": -300.0,
                "descricao": "Notebook",
                "categoria_id": 2,
                "natureza": "Recorrente",
                "parcela_atual": 2,
                "total_parcelas": 5,
            },
        ]
        virtuais = _gerar_virtuais(transacoes, date(2026, 7, 31), hoje=hoje)
        assert len(virtuais) == 3  # parcelas 3, 4, 5
        assert "(3/5)" in virtuais[0]["descricao"]
        assert "(4/5)" in virtuais[1]["descricao"]
        assert "(5/5)" in virtuais[2]["descricao"]


class TestProjecaoEsporadica:
    """Testes para despesas esporádicas — não devem gerar projeções."""

    def test_despesa_esporadica_nao_projeta(self):
        """Despesa esporádica não gera projeções futuras."""
        hoje = date(2026, 3, 7)
        transacoes = [
            {
                "data": date(2026, 3, 5),
                "valor": -500.0,
                "status": "Executada",
                "descricao": "Presente aniversário",
                "categoria_id": 20,
                "natureza": "Esporádica",
            },
        ]
        resultado = calcular_projecao_sync(
            saldo_inicial=5000.0,
            transacoes=transacoes,
            data_inicio=date(2026, 3, 1),
            data_fim=date(2026, 6, 30),
            hoje=hoje,
        )
        movs = [p for p in resultado if p["movimentacao"] != 0]
        assert len(movs) == 1
        assert movs[0]["data"] == "2026-03-05"
        assert resultado[-1]["saldo"] == 4500.0

    def test_esporadica_nao_gera_virtuais(self):
        """_gerar_virtuais deve retornar vazio para esporádica."""
        hoje = date(2026, 3, 7)
        transacoes = [
            {
                "data": date(2026, 3, 5),
                "valor": -200.0,
                "descricao": "Viagem",
                "categoria_id": 21,
                "natureza": "Esporádica",
            },
        ]
        virtuais = _gerar_virtuais(transacoes, date(2026, 6, 30), hoje=hoje)
        assert len(virtuais) == 0

    def test_mix_esporadica_e_fixa(self):
        """Esporádica não interfere na projeção de despesas fixas."""
        hoje = date(2026, 3, 7)
        transacoes = [
            {
                "data": date(2026, 3, 5),
                "valor": -1500.0,
                "status": "Executada",
                "descricao": "Aluguel",
                "categoria_id": 1,
                "natureza": "Fixa",
            },
            {
                "data": date(2026, 3, 10),
                "valor": -300.0,
                "status": "Executada",
                "descricao": "Presente",
                "categoria_id": 20,
                "natureza": "Esporádica",
            },
        ]
        resultado = calcular_projecao_sync(
            saldo_inicial=10000.0,
            transacoes=transacoes,
            data_inicio=date(2026, 3, 1),
            data_fim=date(2026, 5, 31),
            hoje=hoje,
        )
        movs = {p["data"]: p["movimentacao"] for p in resultado if p["movimentacao"] != 0}
        # Aluguel projeta: abril e maio
        assert movs["2026-04-05"] == -1500.0
        assert movs["2026-05-05"] == -1500.0
        # Presente NÃO projeta
        assert "2026-04-10" not in movs
        assert "2026-05-10" not in movs


class TestProjecaoVariavelMedia:
    """Testes para projeção de despesas variáveis por média da categoria."""

    def test_variavel_media_dois_meses(self):
        """Média de dois meses é usada para projeção."""
        hoje = date(2026, 3, 7)
        transacoes = [
            {
                "data": date(2026, 1, 10),
                "valor": -400.0,
                "descricao": "Supermercado",
                "categoria_id": 3,
                "natureza": "Variável",
            },
            {
                "data": date(2026, 2, 10),
                "valor": -600.0,
                "descricao": "Supermercado",
                "categoria_id": 3,
                "natureza": "Variável",
            },
        ]
        virtuais = _gerar_virtuais(transacoes, date(2026, 5, 31), hoje=hoje)
        # Média: (-400 + -600) / 2 = -500. Projeções em abril e maio (março = mês atual)
        assert len(virtuais) == 2
        assert all(v["valor"] == -500.0 for v in virtuais)
        assert all(v["virtual"] is True for v in virtuais)
        assert "média" in virtuais[0]["descricao"]

    def test_variavel_so_mes_atual_usa_como_base(self):
        """Se só há dados no mês corrente, usa esses dados como média."""
        hoje = date(2026, 3, 7)
        transacoes = [
            {
                "data": date(2026, 3, 2),
                "valor": -300.0,
                "descricao": "Alimentação",
                "categoria_id": 5,
                "natureza": "Variável",
            },
        ]
        virtuais = _gerar_virtuais(transacoes, date(2026, 5, 31), hoje=hoje)
        # Sem meses completos, usa o mês atual: -300
        assert len(virtuais) == 2  # abril e maio
        assert all(v["valor"] == -300.0 for v in virtuais)

    def test_variavel_agrupa_por_categoria(self):
        """Transações de mesma categoria com descrições diferentes são agrupadas."""
        hoje = date(2026, 3, 7)
        transacoes = [
            {
                "data": date(2026, 1, 5),
                "valor": -100.0,
                "descricao": "Uber",
                "categoria_id": 4,
                "natureza": "Variável",
            },
            {
                "data": date(2026, 1, 15),
                "valor": -50.0,
                "descricao": "Gasolina",
                "categoria_id": 4,
                "natureza": "Variável",
            },
            {
                "data": date(2026, 2, 10),
                "valor": -200.0,
                "descricao": "Uber",
                "categoria_id": 4,
                "natureza": "Variável",
            },
        ]
        virtuais = _gerar_virtuais(transacoes, date(2026, 5, 31), hoje=hoje)
        # Jan: -100 + -50 = -150. Fev: -200. Média = (-150 + -200)/2 = -175
        # Deve gerar UMA projeção por mês (por categoria, não por descrição)
        datas_virtuais = [v["data"] for v in virtuais]
        meses = set((d.year, d.month) for d in datas_virtuais)
        assert len(meses) == 2  # abril e maio
        assert all(v["valor"] == -175.0 for v in virtuais)

    def test_variavel_nao_duplica_mes_com_real(self):
        """Variável não projeta para meses que já têm transações reais na categoria."""
        hoje = date(2026, 3, 7)
        transacoes = [
            {
                "data": date(2026, 1, 5),
                "valor": -400.0,
                "descricao": "Supermercado",
                "categoria_id": 3,
                "natureza": "Variável",
            },
            {
                "data": date(2026, 2, 5),
                "valor": -600.0,
                "descricao": "Supermercado",
                "categoria_id": 3,
                "natureza": "Variável",
            },
            # Abril já tem transação real
            {
                "data": date(2026, 4, 5),
                "valor": -500.0,
                "descricao": "Supermercado",
                "categoria_id": 3,
                "natureza": "Variável",
            },
        ]
        virtuais = _gerar_virtuais(transacoes, date(2026, 5, 31), hoje=hoje)
        # Abril já tem real, então só projeta maio
        datas = [v["data"] for v in virtuais]
        meses = [(d.year, d.month) for d in datas]
        assert (2026, 4) not in meses
        assert (2026, 5) in meses

    def test_variavel_receita_projeta_positivo(self):
        """Receita variável (ex: freelance) projeta a média positiva."""
        hoje = date(2026, 3, 7)
        transacoes = [
            {
                "data": date(2026, 1, 15),
                "valor": 2000.0,
                "descricao": "Freelance",
                "categoria_id": 30,
                "natureza": "Variável",
            },
            {
                "data": date(2026, 2, 15),
                "valor": 3000.0,
                "descricao": "Freelance",
                "categoria_id": 30,
                "natureza": "Variável",
            },
        ]
        virtuais = _gerar_virtuais(transacoes, date(2026, 5, 31), hoje=hoje)
        # Média = (2000 + 3000)/2 = 2500
        assert len(virtuais) == 2
        assert all(v["valor"] == 2500.0 for v in virtuais)


class TestCalcularMediaMensal:
    """Testes para _calcular_media_mensal."""

    def test_media_basica(self):
        """Média simples de dois meses."""
        hoje = date(2026, 3, 7)
        transacoes = [
            {"data": date(2026, 1, 5), "valor": -400.0},
            {"data": date(2026, 2, 5), "valor": -600.0},
        ]
        assert _calcular_media_mensal(transacoes, hoje) == -500.0

    def test_media_exclui_mes_atual(self):
        """Dados do mês corrente são excluídos por estarem incompletos."""
        hoje = date(2026, 3, 7)
        transacoes = [
            {"data": date(2026, 1, 5), "valor": -400.0},
            {"data": date(2026, 2, 5), "valor": -600.0},
            {"data": date(2026, 3, 2), "valor": -100.0},  # mês atual — excluído
        ]
        # Média = (-400 + -600) / 2 = -500 (março descartado)
        assert _calcular_media_mensal(transacoes, hoje) == -500.0

    def test_media_somente_mes_atual_usa_fallback(self):
        """Se só há dados do mês corrente, usa como fallback."""
        hoje = date(2026, 3, 7)
        transacoes = [
            {"data": date(2026, 3, 2), "valor": -200.0},
            {"data": date(2026, 3, 5), "valor": -100.0},
        ]
        # Fallback: (-200 + -100) / 1 mês = -300
        assert _calcular_media_mensal(transacoes, hoje) == -300.0

    def test_media_sem_transacoes(self):
        """Sem transações retorna 0."""
        hoje = date(2026, 3, 7)
        assert _calcular_media_mensal([], hoje) == 0.0

    def test_media_multiplas_transacoes_mesmo_mes(self):
        """Múltiplas transações no mesmo mês são somadas antes de calcular média."""
        hoje = date(2026, 3, 7)
        transacoes = [
            {"data": date(2026, 1, 5), "valor": -100.0},
            {"data": date(2026, 1, 15), "valor": -200.0},
            {"data": date(2026, 1, 25), "valor": -300.0},
            {"data": date(2026, 2, 10), "valor": -400.0},
        ]
        # Jan: -600, Fev: -400. Média = (-600 + -400)/2 = -500
        assert _calcular_media_mensal(transacoes, hoje) == -500.0