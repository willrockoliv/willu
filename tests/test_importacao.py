"""
Testes unitários para o serviço de importação de extratos (CSV e OFX).
"""

import pytest
from datetime import date, datetime
from unittest.mock import MagicMock, patch
from app.services.importacao import importar_csv, importar_ofx, detectar_formato


class TestImportacaoCSV:
    """Testes para importação de CSV."""

    def test_importar_csv_basico(self):
        """Deve parsear CSV com formato padrão brasileiro."""
        conteudo = (
            "Data;Descrição;Valor\n"
            "05-03-2026;PGTO ALUGUEL;xpto;-1500,00\n"
            "06-03-2026;PIX RECEBIDO;xpto;3000,50\n"
        ).encode("utf-8")

        linhas = importar_csv(conteudo)
        assert len(linhas) == 2

        assert linhas[0].data == date(2026, 3, 5)
        assert linhas[0].descricao == "PGTO ALUGUEL"
        assert linhas[0].valor == -1500.00

        assert linhas[1].data == date(2026, 3, 6)
        assert linhas[1].descricao == "PIX RECEBIDO"
        assert linhas[1].valor == 3000.50

    def test_importar_csv_com_valores_com_ponto_milhar(self):
        """Deve lidar com pontos de milhar no valor."""
        conteudo = (
            "Data;Desc;Valor\n"
            "10-03-2026;SALARIO;xpto;5.000,00\n"
        ).encode("utf-8")

        linhas = importar_csv(conteudo)
        assert len(linhas) == 1
        assert linhas[0].valor == 5000.00

    def test_importar_csv_pular_linhas_invalidas(self):
        """Deve pular linhas com formato inválido."""
        conteudo = (
            "Data;Desc;Valor\n"
            "05-03-2026;ALUGUEL;xpto;-1500,00\n"
            "INVALIDA;TESTE\n"
            "06-03-2026;PIX;xpto;500,00\n"
        ).encode("utf-8")

        linhas = importar_csv(conteudo)
        assert len(linhas) == 2

    def test_importar_csv_vazio(self):
        """CSV sem dados deve retornar lista vazia."""
        conteudo = "Data;Desc;Valor\n".encode("utf-8")
        linhas = importar_csv(conteudo)
        assert len(linhas) == 0

    def test_importar_csv_sem_cabecalho(self):
        """CSV sem cabeçalho deve parsear todas as linhas."""
        conteudo = (
            "05-03-2026;PGTO ALUGUEL;xpto;-1500,00\n"
            "06-03-2026;PIX RECEBIDO;xpto;3000,50\n"
        ).encode("utf-8")

        linhas = importar_csv(conteudo, pular_cabecalho=False)
        assert len(linhas) == 2

    def test_importar_csv_delimitador_customizado(self):
        """Deve funcionar com delimitador vírgula."""
        conteudo = (
            "Data,Desc,Extra,Valor\n"
            "05-03-2026,ALUGUEL,X,-1500.00\n"
        ).encode("utf-8")

        linhas = importar_csv(
            conteudo, delimitador=",", formato_data="%d-%m-%Y",
        )
        assert len(linhas) == 1
        assert linhas[0].descricao == "ALUGUEL"

    def test_importar_csv_formato_data_customizado(self):
        """Deve suportar formato de data DD/MM/YYYY."""
        conteudo = (
            "Data;Desc;Extra;Valor\n"
            "05/03/2026;ALUGUEL;X;-1500,00\n"
        ).encode("utf-8")

        linhas = importar_csv(conteudo, formato_data="%d/%m/%Y")
        assert len(linhas) == 1
        assert linhas[0].data == date(2026, 3, 5)

    def test_importar_csv_encoding_latin1(self):
        """Deve suportar encoding latin-1 para bancos mais antigos."""
        conteudo = (
            "Data;Descrição;Extra;Valor\n"
            "05-03-2026;PAGAMENTO;X;-200,00\n"
        ).encode("latin-1")

        linhas = importar_csv(conteudo, encoding="latin-1")
        assert len(linhas) == 1
        assert linhas[0].valor == -200.0

    def test_importar_csv_colunas_customizadas(self):
        """Deve suportar diferentes posições de coluna."""
        conteudo = (
            "Extra;Data;Valor;Descricao\n"
            "X;05-03-2026;-500,00;INTERNET\n"
        ).encode("utf-8")

        linhas = importar_csv(
            conteudo, col_data=1, col_descricao=3, col_valor=2,
        )
        assert len(linhas) == 1
        assert linhas[0].descricao == "INTERNET"
        assert linhas[0].valor == -500.0

    def test_importar_csv_valor_centavos(self):
        """Valores com centavos devem ser preservados."""
        conteudo = (
            "Data;Desc;Extra;Valor\n"
            "10-03-2026;COMPRA;X;-49,99\n"
        ).encode("utf-8")

        linhas = importar_csv(conteudo)
        assert len(linhas) == 1
        assert linhas[0].valor == -49.99


# ───────────────────────────── OFX ─────────────────────────────


class TestImportacaoOFX:
    """Testes para importação de OFX (usando mock do ofxparse)."""

    def _make_mock_txn(self, dt, memo, amount, payee=None):
        """Helper para criar mock de transação OFX."""
        txn = MagicMock()
        txn.date = dt
        txn.memo = memo
        txn.payee = payee
        txn.amount = amount
        return txn

    def _make_mock_ofx(self, transactions):
        """Helper para criar mock de objeto OFX completo."""
        mock_statement = MagicMock()
        mock_statement.transactions = transactions
        mock_account = MagicMock()
        mock_account.statement = mock_statement
        mock_ofx = MagicMock()
        mock_ofx.accounts = [mock_account]
        # Garantir que hasattr(ofx, "accounts") retorne True
        mock_ofx.__contains__ = lambda self, item: item == "accounts"
        return mock_ofx

    def test_importar_ofx_basico(self):
        """Deve parsear transações OFX e retornar LinhaExtrato."""
        txns = [
            self._make_mock_txn(datetime(2026, 3, 5), "PGTO ALUGUEL", -1500.0),
            self._make_mock_txn(datetime(2026, 3, 6), "PIX RECEBIDO", 3000.50),
        ]
        mock_ofx = self._make_mock_ofx(txns)

        with patch("app.services.importacao.OfxParser.parse", return_value=mock_ofx):
            linhas = importar_ofx(b"dummy")

        assert len(linhas) == 2
        assert linhas[0].data == date(2026, 3, 5)
        assert linhas[0].descricao == "PGTO ALUGUEL"
        assert linhas[0].valor == -1500.0
        assert linhas[1].data == date(2026, 3, 6)
        assert linhas[1].valor == 3000.50

    def test_importar_ofx_usa_payee_quando_memo_vazio(self):
        """Quando memo é None, deve usar payee como descrição."""
        txns = [
            self._make_mock_txn(datetime(2026, 3, 5), None, -200.0, payee="RESTAURANTE XYZ"),
        ]
        mock_ofx = self._make_mock_ofx(txns)

        with patch("app.services.importacao.OfxParser.parse", return_value=mock_ofx):
            linhas = importar_ofx(b"dummy")

        assert len(linhas) == 1
        assert linhas[0].descricao == "RESTAURANTE XYZ"

    def test_importar_ofx_descricao_vazia(self):
        """Quando memo e payee são None, descrição deve ser string vazia."""
        txns = [
            self._make_mock_txn(datetime(2026, 3, 5), None, -50.0, payee=None),
        ]
        mock_ofx = self._make_mock_ofx(txns)

        with patch("app.services.importacao.OfxParser.parse", return_value=mock_ofx):
            linhas = importar_ofx(b"dummy")

        assert len(linhas) == 1
        assert linhas[0].descricao == ""

    def test_importar_ofx_conta_sem_statement(self):
        """Conta sem statement deve ser ignorada."""
        mock_account = MagicMock()
        mock_account.statement = None
        mock_ofx = MagicMock()
        mock_ofx.accounts = [mock_account]

        with patch("app.services.importacao.OfxParser.parse", return_value=mock_ofx):
            linhas = importar_ofx(b"dummy")

        assert len(linhas) == 0

    def test_importar_ofx_data_como_date(self):
        """Deve lidar com data já como date (não datetime)."""
        txns = [
            self._make_mock_txn(date(2026, 3, 5), "COMPRA", -100.0),
        ]
        mock_ofx = self._make_mock_ofx(txns)

        with patch("app.services.importacao.OfxParser.parse", return_value=mock_ofx):
            linhas = importar_ofx(b"dummy")

        assert len(linhas) == 1
        assert linhas[0].data == date(2026, 3, 5)

    def test_importar_ofx_multiplas_contas(self):
        """Deve processar transações de múltiplas contas."""
        txn1 = self._make_mock_txn(datetime(2026, 3, 1), "CONTA1", -100.0)
        txn2 = self._make_mock_txn(datetime(2026, 3, 2), "CONTA2", -200.0)

        stmt1 = MagicMock()
        stmt1.transactions = [txn1]
        stmt2 = MagicMock()
        stmt2.transactions = [txn2]

        acct1 = MagicMock()
        acct1.statement = stmt1
        acct2 = MagicMock()
        acct2.statement = stmt2

        mock_ofx = MagicMock()
        mock_ofx.accounts = [acct1, acct2]

        with patch("app.services.importacao.OfxParser.parse", return_value=mock_ofx):
            linhas = importar_ofx(b"dummy")

        assert len(linhas) == 2


class TestDetectarFormato:
    """Testes para detecção de formato de arquivo."""

    def test_detectar_ofx(self):
        assert detectar_formato("extrato.ofx") == "ofx"
        assert detectar_formato("BANCO.OFX") == "ofx"

    def test_detectar_csv(self):
        assert detectar_formato("extrato.csv") == "csv"
        assert detectar_formato("DADOS.CSV") == "csv"

    def test_formato_nao_suportado(self):
        with pytest.raises(ValueError):
            detectar_formato("arquivo.pdf")

        with pytest.raises(ValueError):
            detectar_formato("arquivo.xlsx")

    def test_detectar_formato_com_caminho(self):
        """Deve funcionar com caminho completo, não apenas nome."""
        assert detectar_formato("/tmp/uploads/extrato.ofx") == "ofx"
        assert detectar_formato("C:\\Users\\data\\banco.csv") == "csv"

    def test_formato_sem_extensao(self):
        """Arquivo sem extensão reconhecível deve dar erro."""
        with pytest.raises(ValueError):
            detectar_formato("arquivo")
        with pytest.raises(ValueError):
            detectar_formato("arquivo.txt")
