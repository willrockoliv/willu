"""
Testes unitários para o motor de conciliação inteligente.
Foca no algoritmo de matching: Dicionário → Fuzzy → Palavras-chave.
"""

import pytest
from datetime import date
from app.schemas.conciliacao import LinhaExtrato
from app.services.conciliacao import conciliar_linha_sync


class TestConciliacaoDicionario:
    """Testes para match via dicionário histórico (prioridade 1)."""

    def test_match_exato_dicionario(self):
        """Quando a descrição do banco está no dicionário, deve dar match automático."""
        linha = LinhaExtrato(data=date(2026, 3, 5), descricao="PGTO ALUGUEL 12345", valor=-1500.0)
        dicionario = {
            "PGTO ALUGUEL 12345": {
                "categoria_id": 1,
                "categoria_nome": "Aluguel",
                "descricao_padrao": "Aluguel Apartamento",
            }
        }
        resultado = conciliar_linha_sync(linha, [], dicionario, [])

        assert resultado.origem == "dicionario"
        assert resultado.score == 100.0
        assert resultado.categoria_id == 1
        assert resultado.transacao_descricao == "Aluguel Apartamento"

    def test_sem_match_dicionario(self):
        """Quando a descrição não está no dicionário, não deve dar match por dicionário."""
        linha = LinhaExtrato(data=date(2026, 3, 5), descricao="COMPRA DESCONHECIDA", valor=-50.0)
        dicionario = {
            "PGTO ALUGUEL 12345": {"categoria_id": 1, "categoria_nome": "Aluguel"},
        }
        resultado = conciliar_linha_sync(linha, [], dicionario, [])
        assert resultado.origem != "dicionario"


class TestConciliacaoFuzzy:
    """Testes para match fuzzy (prioridade 2)."""

    def test_match_fuzzy_valor_e_data_exatos(self):
        """Match perfeito: mesmo valor e mesma data."""
        linha = LinhaExtrato(data=date(2026, 3, 5), descricao="PGTO ALUGUEL", valor=-1500.0)
        transacoes = [
            {
                "id": 10,
                "descricao": "Aluguel",
                "valor_previsto": -1500.0,
                "data_vencimento": date(2026, 3, 5),
                "categoria_id": 1,
                "categoria_nome": "Aluguel",
            }
        ]
        resultado = conciliar_linha_sync(linha, transacoes, {}, [])

        assert resultado.origem == "fuzzy"
        assert resultado.transacao_id == 10
        assert resultado.score >= 65

    def test_match_fuzzy_com_tolerancia_data(self):
        """Deve encontrar match com até 3 dias de diferença."""
        linha = LinhaExtrato(data=date(2026, 3, 7), descricao="PGTO ALUGUEL", valor=-1500.0)
        transacoes = [
            {
                "id": 10,
                "descricao": "Aluguel",
                "valor_previsto": -1500.0,
                "data_vencimento": date(2026, 3, 5),
                "categoria_id": 1,
                "categoria_nome": "Aluguel",
            }
        ]
        resultado = conciliar_linha_sync(linha, transacoes, {}, [])

        assert resultado.origem == "fuzzy"
        assert resultado.transacao_id == 10

    def test_match_fuzzy_com_tolerancia_valor(self):
        """Deve encontrar match com até 5% de diferença no valor."""
        linha = LinhaExtrato(data=date(2026, 3, 5), descricao="ENERGIA", valor=-155.0)
        transacoes = [
            {
                "id": 20,
                "descricao": "Energia Elétrica",
                "valor_previsto": -150.0,
                "data_vencimento": date(2026, 3, 5),
                "categoria_id": 7,
                "categoria_nome": "Energia Elétrica",
            }
        ]
        resultado = conciliar_linha_sync(linha, transacoes, {}, [])

        # 155 vs 150 = 3.3% de diferença — dentro da tolerância
        assert resultado.origem == "fuzzy"
        assert resultado.transacao_id == 20

    def test_sem_match_fuzzy_fora_tolerancia(self):
        """Não deve dar match se valor e data estiverem muito distantes."""
        linha = LinhaExtrato(data=date(2026, 3, 15), descricao="COMPRA", valor=-500.0)
        transacoes = [
            {
                "id": 30,
                "descricao": "Aluguel",
                "valor_previsto": -1500.0,
                "data_vencimento": date(2026, 3, 5),
                "categoria_id": 1,
                "categoria_nome": "Aluguel",
            }
        ]
        resultado = conciliar_linha_sync(linha, transacoes, {}, [])
        assert resultado.origem != "fuzzy"

    def test_match_fuzzy_melhor_candidato(self):
        """Deve escolher a transação com melhor score entre múltiplas candidatas."""
        linha = LinhaExtrato(data=date(2026, 3, 10), descricao="INTERNET FIBRA", valor=-120.0)
        transacoes = [
            {
                "id": 40,
                "descricao": "Internet",
                "valor_previsto": -119.90,
                "data_vencimento": date(2026, 3, 10),
                "categoria_id": 9,
                "categoria_nome": "Internet",
            },
            {
                "id": 41,
                "descricao": "Celular",
                "valor_previsto": -89.90,
                "data_vencimento": date(2026, 3, 12),
                "categoria_id": 10,
                "categoria_nome": "Celular",
            },
        ]
        resultado = conciliar_linha_sync(linha, transacoes, {}, [])

        assert resultado.transacao_id == 40  # Internet é o melhor match


class TestConciliacaoPalavrasChave:
    """Testes para match por palavras-chave (prioridade 3)."""

    def test_match_palavras_chave(self):
        """Deve sugerir categoria quando descrição é similar ao nome da categoria."""
        linha = LinhaExtrato(data=date(2026, 3, 5), descricao="SUPERMERCADO EXTRA", valor=-250.0)
        categorias = [
            {"id": 14, "nome": "Supermercado"},
            {"id": 16, "nome": "Lazer"},
        ]
        resultado = conciliar_linha_sync(linha, [], {}, categorias)

        assert resultado.origem == "palavras_chave"
        assert resultado.categoria_id == 14

    def test_sem_match_palavras_chave(self):
        """Quando descrição não é similar a nenhuma categoria → 'nova'."""
        linha = LinhaExtrato(data=date(2026, 3, 5), descricao="XYZABC123", valor=-10.0)
        categorias = [
            {"id": 14, "nome": "Supermercado"},
            {"id": 16, "nome": "Lazer"},
        ]
        resultado = conciliar_linha_sync(linha, [], {}, categorias)

        assert resultado.origem == "nova"
        assert resultado.score == 0.0


class TestConciliacaoPrioridade:
    """Testes para verificar ordem de prioridade do motor."""

    def test_dicionario_tem_prioridade_sobre_fuzzy(self):
        """Dicionário deve ter prioridade sobre fuzzy match."""
        linha = LinhaExtrato(data=date(2026, 3, 5), descricao="PGTO ALUGUEL 12345", valor=-1500.0)
        dicionario = {
            "PGTO ALUGUEL 12345": {
                "categoria_id": 1,
                "categoria_nome": "Aluguel",
                "descricao_padrao": "Aluguel via dicionário",
            }
        }
        transacoes = [
            {
                "id": 10,
                "descricao": "Aluguel",
                "valor_previsto": -1500.0,
                "data_vencimento": date(2026, 3, 5),
                "categoria_id": 1,
                "categoria_nome": "Aluguel",
            }
        ]
        resultado = conciliar_linha_sync(linha, transacoes, dicionario, [])

        # Dicionário tem prioridade
        assert resultado.origem == "dicionario"
        assert resultado.score == 100.0

    def test_transacao_nova_quando_nenhum_match(self):
        """Quando nenhum método encontra match, deve retornar 'nova'."""
        linha = LinhaExtrato(data=date(2026, 3, 5), descricao="TRANSACAO ALEATORIA 999", valor=-42.0)
        resultado = conciliar_linha_sync(linha, [], {}, [])

        assert resultado.origem == "nova"
        assert resultado.transacao_id is None
        assert resultado.categoria_id is None
        assert resultado.score == 0.0


class TestConciliacaoEdgeCases:
    """Testes de edge cases para o motor de conciliação."""

    def test_dicionario_com_whitespace(self):
        """Descrição com espaços deve ser tratada (strip)."""
        linha = LinhaExtrato(data=date(2026, 3, 5), descricao="  PGTO ALUGUEL  ", valor=-1500.0)
        dicionario = {
            "PGTO ALUGUEL": {
                "categoria_id": 1,
                "categoria_nome": "Aluguel",
                "descricao_padrao": "Aluguel",
            }
        }
        resultado = conciliar_linha_sync(linha, [], dicionario, [])

        assert resultado.origem == "dicionario"
        assert resultado.score == 100.0

    def test_fuzzy_com_valor_previsto_zero(self):
        """Transação com valor_previsto=0 não deve causar divisão por zero."""
        linha = LinhaExtrato(data=date(2026, 3, 5), descricao="AJUSTE", valor=-10.0)
        transacoes = [
            {
                "id": 50,
                "descricao": "Ajuste",
                "valor_previsto": 0.0,
                "data_vencimento": date(2026, 3, 5),
                "categoria_id": 1,
                "categoria_nome": "Ajuste",
            }
        ]
        # Não deve levantar exceção
        resultado = conciliar_linha_sync(linha, transacoes, {}, [])
        # Score de valor será 0, mas data (30) + texto podem somar
        assert resultado is not None

    def test_fuzzy_score_maximo_com_match_perfeito(self):
        """Match perfeito (valor exato + data exata + texto idêntico) deve ter score alto."""
        linha = LinhaExtrato(data=date(2026, 3, 5), descricao="Aluguel", valor=-1500.0)
        transacoes = [
            {
                "id": 10,
                "descricao": "Aluguel",
                "valor_previsto": -1500.0,
                "data_vencimento": date(2026, 3, 5),
                "categoria_id": 1,
                "categoria_nome": "Aluguel",
            }
        ]
        resultado = conciliar_linha_sync(linha, transacoes, {}, [])

        assert resultado.origem == "fuzzy"
        # Score perfeito: valor(50) + data(30) + texto(20) = 100
        assert resultado.score == 100.0

    def test_fuzzy_nao_matcha_fora_janela_dias(self):
        """Transação fora da janela de ±3 dias não deve ser candidata."""
        linha = LinhaExtrato(data=date(2026, 3, 10), descricao="ALUGUEL", valor=-1500.0)
        transacoes = [
            {
                "id": 10,
                "descricao": "Aluguel",
                "valor_previsto": -1500.0,
                "data_vencimento": date(2026, 3, 1),  # 9 dias de diferença
                "categoria_id": 1,
                "categoria_nome": "Aluguel",
            }
        ]
        resultado = conciliar_linha_sync(linha, transacoes, {}, [])
        assert resultado.origem != "fuzzy"

    def test_palavras_chave_case_insensitive(self):
        """Match por palavras-chave deve ser case-insensitive."""
        linha = LinhaExtrato(data=date(2026, 3, 5), descricao="supermercado carrefour", valor=-350.0)
        categorias = [
            {"id": 14, "nome": "SUPERMERCADO"},
        ]
        resultado = conciliar_linha_sync(linha, [], {}, categorias)

        assert resultado.origem == "palavras_chave"
        assert resultado.categoria_id == 14

    def test_linha_extrato_preservada_no_resultado(self):
        """A linha de extrato original deve ser preservada no resultado."""
        linha = LinhaExtrato(data=date(2026, 3, 5), descricao="COMPRA PIX", valor=-99.90)
        resultado = conciliar_linha_sync(linha, [], {}, [])

        assert resultado.linha_extrato.data == date(2026, 3, 5)
        assert resultado.linha_extrato.descricao == "COMPRA PIX"
        assert resultado.linha_extrato.valor == -99.90

    def test_fuzzy_prioridade_sobre_palavras_chave(self):
        """Fuzzy match deve ter prioridade sobre palavras-chave."""
        linha = LinhaExtrato(data=date(2026, 3, 5), descricao="ENERGIA ELETRICA", valor=-150.0)
        transacoes = [
            {
                "id": 20,
                "descricao": "Energia Elétrica",
                "valor_previsto": -150.0,
                "data_vencimento": date(2026, 3, 5),
                "categoria_id": 7,
                "categoria_nome": "Energia Elétrica",
            }
        ]
        categorias = [
            {"id": 7, "nome": "Energia Elétrica"},
        ]
        resultado = conciliar_linha_sync(linha, transacoes, {}, categorias)

        # Fuzzy tem prioridade sobre palavras-chave
        assert resultado.origem == "fuzzy"
        assert resultado.transacao_id == 20
