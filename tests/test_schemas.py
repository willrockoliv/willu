"""
Testes unitários para validação dos schemas Pydantic.
Garante que validações, defaults e conversão de tipos funcionam corretamente.
"""

import pytest
from datetime import date
from pydantic import ValidationError

from app.schemas.conta import ContaCreate, ContaUpdate, ContaRead
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate, CategoriaRead
from app.schemas.transacao import TransacaoCreate, TransacaoUpdate, TransacaoRead
from app.schemas.conciliacao import (
    LinhaExtrato,
    SugestaoConciliacao,
    ConfirmacaoConciliacao,
)
from app.models.categoria import TipoCategoria, NaturezaCategoria
from app.models.transacao import StatusTransacao


# ───────────────────────────── Conta ─────────────────────────────


class TestContaSchemas:
    """Testes para schemas de Conta."""

    def test_conta_create_valida(self):
        conta = ContaCreate(nome="Nubank", saldo_inicial=1500.50)
        assert conta.nome == "Nubank"
        assert conta.saldo_inicial == 1500.50

    def test_conta_create_saldo_default_zero(self):
        """Saldo inicial deve ter default 0.0."""
        conta = ContaCreate(nome="Carteira")
        assert conta.saldo_inicial == 0.0

    def test_conta_create_sem_nome_rejeita(self):
        """Nome é obrigatório."""
        with pytest.raises(ValidationError):
            ContaCreate()

    def test_conta_create_saldo_negativo_aceita(self):
        """Saldo negativo é válido (conta no cheque especial)."""
        conta = ContaCreate(nome="Itaú", saldo_inicial=-500.0)
        assert conta.saldo_inicial == -500.0

    def test_conta_update_parcial(self):
        """Update deve aceitar campos individuais."""
        update = ContaUpdate(nome="Novo Nome")
        assert update.nome == "Novo Nome"
        assert update.saldo_inicial is None

    def test_conta_update_vazio(self):
        """Update sem campos deve ter tudo None."""
        update = ContaUpdate()
        assert update.nome is None
        assert update.saldo_inicial is None

    def test_conta_read_from_attributes(self):
        """ContaRead deve converter objeto ORM automaticamente."""
        class FakeConta:
            id = 1
            nome = "Itaú"
            saldo_inicial = 500.0

        conta = ContaRead.model_validate(FakeConta())
        assert conta.id == 1
        assert conta.nome == "Itaú"
        assert conta.saldo_inicial == 500.0


# ───────────────────────────── Categoria ─────────────────────────────


class TestCategoriaSchemas:
    """Testes para schemas de Categoria."""

    def test_categoria_create_valida(self):
        cat = CategoriaCreate(
            nome="Aluguel",
            tipo=TipoCategoria.DESPESA,
            natureza=NaturezaCategoria.FIXA,
        )
        assert cat.nome == "Aluguel"
        assert cat.tipo == TipoCategoria.DESPESA
        assert cat.natureza == NaturezaCategoria.FIXA

    def test_categoria_create_com_valores_string(self):
        """Deve aceitar valores string que correspondem ao enum."""
        cat = CategoriaCreate(nome="Salário", tipo="Receita", natureza="Fixa")
        assert cat.tipo == TipoCategoria.RECEITA
        assert cat.natureza == NaturezaCategoria.FIXA

    def test_categoria_create_enum_invalido_rejeita(self):
        """Enum inválido deve levantar ValidationError."""
        with pytest.raises(ValidationError):
            CategoriaCreate(nome="Teste", tipo="INVALIDO", natureza="INVALIDO")

    def test_categoria_create_sem_campos_rejeita(self):
        """Todos os campos são obrigatórios."""
        with pytest.raises(ValidationError):
            CategoriaCreate(nome="Apenas nome")

    def test_categoria_update_parcial(self):
        update = CategoriaUpdate(nome="Novo Nome")
        assert update.nome == "Novo Nome"
        assert update.tipo is None
        assert update.natureza is None

    def test_categoria_read_from_attributes(self):
        class FakeCategoria:
            id = 5
            nome = "Energia"
            tipo = TipoCategoria.DESPESA
            natureza = NaturezaCategoria.RECORRENTE

        cat = CategoriaRead.model_validate(FakeCategoria())
        assert cat.id == 5
        assert cat.nome == "Energia"
        assert cat.tipo == TipoCategoria.DESPESA
        assert cat.natureza == NaturezaCategoria.RECORRENTE


# ───────────────────────────── Transação ─────────────────────────────


class TestTransacaoSchemas:
    """Testes para schemas de Transação."""

    def test_transacao_create_minima(self):
        """Apenas campos obrigatórios."""
        t = TransacaoCreate(
            conta_id=1,
            valor_previsto=-150.0,
            data_vencimento=date(2026, 3, 10),
            descricao="Energia",
        )
        assert t.conta_id == 1
        assert t.status == StatusTransacao.PROJETADA
        assert t.valor_realizado is None
        assert t.data_pagamento is None
        assert t.categoria_id is None
        assert t.descricao_banco is None

    def test_transacao_create_completa(self):
        """Todos os campos preenchidos."""
        t = TransacaoCreate(
            conta_id=1,
            categoria_id=5,
            valor_previsto=-150.0,
            valor_realizado=-155.30,
            data_vencimento=date(2026, 3, 10),
            data_pagamento=date(2026, 3, 12),
            status=StatusTransacao.EXECUTADA,
            descricao="Energia",
            descricao_banco="CPFL ENERGIA",
        )
        assert t.status == StatusTransacao.EXECUTADA
        assert t.valor_realizado == -155.30
        assert t.descricao_banco == "CPFL ENERGIA"

    def test_transacao_create_sem_campos_obrigatorios_rejeita(self):
        """Sem data_vencimento e descricao deve rejeitar."""
        with pytest.raises(ValidationError):
            TransacaoCreate(conta_id=1, valor_previsto=-100.0)

    def test_transacao_update_parcial(self):
        update = TransacaoUpdate(descricao="Nova descrição")
        assert update.descricao == "Nova descrição"
        assert update.valor_previsto is None
        assert update.conta_id is None

    def test_transacao_update_vazio(self):
        update = TransacaoUpdate()
        assert update.descricao is None
        assert update.status is None

    def test_transacao_read_from_attributes(self):
        class FakeTransacao:
            id = 1
            conta_id = 1
            categoria_id = None
            valor_previsto = -500.0
            valor_realizado = None
            data_vencimento = date(2026, 3, 10)
            data_pagamento = None
            status = StatusTransacao.PROJETADA
            descricao = "Aluguel"
            descricao_banco = None

        t = TransacaoRead.model_validate(FakeTransacao())
        assert t.id == 1
        assert t.status == StatusTransacao.PROJETADA
        assert t.valor_realizado is None

    def test_transacao_create_status_default_projetada(self):
        """Status default deve ser PROJETADA."""
        t = TransacaoCreate(
            conta_id=1,
            valor_previsto=-100.0,
            data_vencimento=date(2026, 3, 1),
            descricao="Teste",
        )
        assert t.status == StatusTransacao.PROJETADA


# ───────────────────────────── Conciliação ─────────────────────────────


class TestConciliacaoSchemas:
    """Testes para schemas de Conciliação."""

    def test_linha_extrato_valida(self):
        linha = LinhaExtrato(
            data=date(2026, 3, 5),
            descricao="PGTO ALUGUEL",
            valor=-1500.0,
        )
        assert linha.data == date(2026, 3, 5)
        assert linha.descricao == "PGTO ALUGUEL"
        assert linha.valor == -1500.0

    def test_linha_extrato_sem_campos_rejeita(self):
        with pytest.raises(ValidationError):
            LinhaExtrato()

    def test_linha_extrato_valor_positivo(self):
        """Receitas (valor positivo) são válidas."""
        linha = LinhaExtrato(data=date(2026, 3, 1), descricao="PIX", valor=500.0)
        assert linha.valor == 500.0

    def test_sugestao_conciliacao_defaults(self):
        """Defaults devem representar sugestão vazia."""
        linha = LinhaExtrato(data=date(2026, 3, 5), descricao="PIX", valor=-50.0)
        sug = SugestaoConciliacao(linha_extrato=linha)
        assert sug.transacao_id is None
        assert sug.transacao_descricao is None
        assert sug.categoria_id is None
        assert sug.categoria_nome is None
        assert sug.score == 0.0
        assert sug.origem == ""
        assert sug.duplicada is False

    def test_sugestao_conciliacao_completa(self):
        linha = LinhaExtrato(data=date(2026, 3, 5), descricao="PIX", valor=-50.0)
        sug = SugestaoConciliacao(
            linha_extrato=linha,
            transacao_id=10,
            transacao_descricao="Pizza",
            categoria_id=14,
            categoria_nome="Alimentação",
            score=85.5,
            origem="fuzzy",
            duplicada=True,
        )
        assert sug.transacao_id == 10
        assert sug.score == 85.5
        assert sug.duplicada is True
        assert sug.origem == "fuzzy"

    def test_confirmacao_conciliacao_valida(self):
        linha = LinhaExtrato(data=date(2026, 3, 5), descricao="PIX", valor=-50.0)
        conf = ConfirmacaoConciliacao(
            linha_extrato=linha,
            transacao_id=10,
            categoria_id=14,
            descricao="Pizza",
            conta_id=1,
        )
        assert conf.salvar_dicionario is True  # default

    def test_confirmacao_conciliacao_sem_dicionario(self):
        linha = LinhaExtrato(data=date(2026, 3, 5), descricao="PIX", valor=-50.0)
        conf = ConfirmacaoConciliacao(
            linha_extrato=linha,
            descricao="Diverso",
            conta_id=1,
            salvar_dicionario=False,
        )
        assert conf.salvar_dicionario is False
        assert conf.transacao_id is None
        assert conf.categoria_id is None

    def test_confirmacao_conciliacao_sem_campos_obrigatorios_rejeita(self):
        """descricao e conta_id são obrigatórios."""
        linha = LinhaExtrato(data=date(2026, 3, 5), descricao="PIX", valor=-50.0)
        with pytest.raises(ValidationError):
            ConfirmacaoConciliacao(linha_extrato=linha)
