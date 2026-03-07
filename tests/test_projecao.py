"""
Testes unitários para o serviço de projeção de saldo.
Foca na lógica de cálculo de saldo dia a dia.
"""

import pytest
from datetime import date, timedelta
from app.services.projecao import calcular_projecao_sync


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
