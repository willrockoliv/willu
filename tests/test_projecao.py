"""
Testes unitários para o serviço de projeção de saldo.
Foca na lógica de cálculo de saldo dia a dia,
incluindo geração de transações virtuais para despesas fixas e recorrentes.
"""

import pytest
from datetime import date, timedelta
from app.services.projecao import calcular_projecao_sync, _add_months, _gerar_virtuais


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

    def test_despesa_variavel_nao_projeta(self):
        """Despesa variável não gera projeções futuras."""
        hoje = date(2026, 3, 7)
        transacoes = [
            {
                "data": date(2026, 3, 5),
                "valor": -200.0,
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
            data_fim=date(2026, 6, 30),
            hoje=hoje,
        )
        # Só uma movimentação no dia 5 de março
        movs = [p for p in resultado if p["movimentacao"] != 0]
        assert len(movs) == 1
        assert movs[0]["data"] == "2026-03-05"
        assert movs[0]["movimentacao"] == -200.0

        # Saldo constante depois do dia 5
        assert resultado[-1]["saldo"] == 4800.0

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
