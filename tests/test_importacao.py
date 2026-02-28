"""
Testes unitários para o serviço de importação de extratos (CSV).
"""

import pytest
from datetime import date
from app.services.importacao import importar_csv, detectar_formato


class TestImportacaoCSV:
    """Testes para importação de CSV."""

    def test_importar_csv_basico(self):
        """Deve parsear CSV com formato padrão brasileiro."""
        conteudo = (
            "Data;Descrição;Valor\n"
            "05/03/2026;PGTO ALUGUEL;-1500,00\n"
            "06/03/2026;PIX RECEBIDO;3000,50\n"
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
            "10/03/2026;SALARIO;5.000,00\n"
        ).encode("utf-8")

        linhas = importar_csv(conteudo)
        assert len(linhas) == 1
        assert linhas[0].valor == 5000.00

    def test_importar_csv_pular_linhas_invalidas(self):
        """Deve pular linhas com formato inválido."""
        conteudo = (
            "Data;Desc;Valor\n"
            "05/03/2026;ALUGUEL;-1500,00\n"
            "INVALIDA;TESTE\n"
            "06/03/2026;PIX;500,00\n"
        ).encode("utf-8")

        linhas = importar_csv(conteudo)
        assert len(linhas) == 2

    def test_importar_csv_vazio(self):
        """CSV sem dados deve retornar lista vazia."""
        conteudo = "Data;Desc;Valor\n".encode("utf-8")
        linhas = importar_csv(conteudo)
        assert len(linhas) == 0


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
