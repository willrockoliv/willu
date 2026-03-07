"""
Testes unitários para lógica dos models SQLAlchemy.
Foca em properties, enums e representações textuais.
"""

import pytest
from datetime import date

from app.models.transacao import Transacao, StatusTransacao
from app.models.categoria import Categoria, TipoCategoria, NaturezaCategoria
from app.models.conta import Conta
from app.models.dicionario_conciliacao import DicionarioConciliacao


# ───────────────────────────── Transacao.valor_efetivo ─────────────────────────────


class TestTransacaoValorEfetivo:
    """Testes para a property valor_efetivo do model Transacao."""

    def test_executada_com_valor_realizado(self):
        """Quando executada e tem valor_realizado, retorna valor_realizado."""
        t = Transacao(
            id=1, conta_id=1, valor_previsto=-150.0, valor_realizado=-155.30,
            data_vencimento=date(2026, 3, 10), status=StatusTransacao.EXECUTADA,
            descricao="Energia",
        )
        assert t.valor_efetivo == -155.30

    def test_executada_sem_valor_realizado(self):
        """Quando executada sem valor_realizado, retorna valor_previsto."""
        t = Transacao(
            id=2, conta_id=1, valor_previsto=-150.0, valor_realizado=None,
            data_vencimento=date(2026, 3, 10), status=StatusTransacao.EXECUTADA,
            descricao="Energia",
        )
        assert t.valor_efetivo == -150.0

    def test_projetada_retorna_valor_previsto(self):
        """Quando projetada, retorna valor_previsto."""
        t = Transacao(
            id=3, conta_id=1, valor_previsto=-1500.0, valor_realizado=None,
            data_vencimento=date(2026, 3, 5), status=StatusTransacao.PROJETADA,
            descricao="Aluguel",
        )
        assert t.valor_efetivo == -1500.0

    def test_projetada_ignora_valor_realizado(self):
        """Mesmo com valor_realizado, se projetada retorna valor_previsto."""
        t = Transacao(
            id=4, conta_id=1, valor_previsto=-1500.0, valor_realizado=-1600.0,
            data_vencimento=date(2026, 3, 5), status=StatusTransacao.PROJETADA,
            descricao="Aluguel",
        )
        assert t.valor_efetivo == -1500.0

    def test_valor_efetivo_zero(self):
        """Valor zero é válido."""
        t = Transacao(
            id=5, conta_id=1, valor_previsto=0.0, valor_realizado=None,
            data_vencimento=date(2026, 3, 5), status=StatusTransacao.PROJETADA,
            descricao="Ajuste",
        )
        assert t.valor_efetivo == 0.0

    def test_valor_efetivo_receita(self):
        """Receita (valor positivo) funciona corretamente."""
        t = Transacao(
            id=6, conta_id=1, valor_previsto=5000.0, valor_realizado=5100.0,
            data_vencimento=date(2026, 3, 5), status=StatusTransacao.EXECUTADA,
            descricao="Salário",
        )
        assert t.valor_efetivo == 5100.0


# ───────────────────────────── __repr__ ─────────────────────────────


class TestModelRepr:
    """Testes para representação textual dos models."""

    def test_repr_transacao(self):
        t = Transacao(
            id=1, conta_id=1, valor_previsto=-100.0,
            data_vencimento=date(2026, 3, 1), status=StatusTransacao.PROJETADA,
            descricao="Teste Repr",
        )
        r = repr(t)
        assert "Transacao" in r
        assert "Teste Repr" in r
        assert "1" in r

    def test_repr_conta(self):
        c = Conta(id=1, nome="Nubank", saldo_inicial=1000.0)
        r = repr(c)
        assert "Conta" in r
        assert "Nubank" in r

    def test_repr_categoria(self):
        c = Categoria(
            id=1, nome="Aluguel",
            tipo=TipoCategoria.DESPESA, natureza=NaturezaCategoria.FIXA,
        )
        r = repr(c)
        assert "Categoria" in r
        assert "Aluguel" in r

    def test_repr_dicionario(self):
        d = DicionarioConciliacao(
            id=1, descricao_banco="PGTO ALUGUEL 12345", categoria_id=1,
        )
        r = repr(d)
        assert "DicionarioConciliacao" in r
        assert "PGTO ALUGUEL 12345" in r


# ───────────────────────────── Enums ─────────────────────────────


class TestEnums:
    """Testes para os enums do sistema."""

    def test_tipo_categoria_values(self):
        assert TipoCategoria.RECEITA.value == "Receita"
        assert TipoCategoria.DESPESA.value == "Despesa"

    def test_natureza_categoria_values(self):
        assert NaturezaCategoria.FIXA.value == "Fixa"
        assert NaturezaCategoria.RECORRENTE.value == "Recorrente"
        assert NaturezaCategoria.VARIAVEL.value == "Variável"
        assert NaturezaCategoria.ESPORADICA.value == "Esporádica"

    def test_status_transacao_values(self):
        assert StatusTransacao.PROJETADA.value == "Projetada"
        assert StatusTransacao.EXECUTADA.value == "Executada"

    def test_enums_sao_strings(self):
        """Enums devem ser instâncias de str para serialização automática."""
        assert isinstance(TipoCategoria.RECEITA, str)
        assert isinstance(NaturezaCategoria.FIXA, str)
        assert isinstance(StatusTransacao.PROJETADA, str)

    def test_tipo_categoria_tem_dois_membros(self):
        assert len(TipoCategoria) == 2

    def test_natureza_categoria_tem_quatro_membros(self):
        assert len(NaturezaCategoria) == 4

    def test_status_transacao_tem_dois_membros(self):
        assert len(StatusTransacao) == 2
