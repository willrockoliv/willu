"""
Serviço de importação de extratos bancários (OFX e CSV).
Parseia os arquivos e retorna uma lista normalizada de LinhaExtrato.
"""

import csv
import io
from datetime import date, datetime
from ofxparse import OfxParser

from app.schemas.conciliacao import LinhaExtrato


def importar_ofx(conteudo: bytes) -> list[LinhaExtrato]:
    """Parseia um arquivo OFX e retorna lista de LinhaExtrato."""
    ofx = OfxParser.parse(io.BytesIO(conteudo))
    linhas = []

    for account in ofx.accounts if hasattr(ofx, "accounts") else [ofx.account]:
        if account.statement is None:
            continue
        for txn in account.statement.transactions:
            linhas.append(
                LinhaExtrato(
                    data=txn.date.date() if isinstance(txn.date, datetime) else txn.date,
                    descricao=txn.memo or txn.payee or "",
                    valor=float(txn.amount),
                )
            )

    return linhas


def importar_csv(
    conteudo: bytes,
    encoding: str = "utf-8",
    delimitador: str = ";",
    col_data: int = 0,
    col_descricao: int = 1,
    col_valor: int = 2,
    formato_data: str = "%d/%m/%Y",
    pular_cabecalho: bool = True,
) -> list[LinhaExtrato]:
    """
    Parseia um arquivo CSV de extrato bancário.
    As colunas são configuráveis para suportar diferentes layouts de bancos.
    """
    texto = conteudo.decode(encoding)
    reader = csv.reader(io.StringIO(texto), delimiter=delimitador)
    linhas = []

    for i, row in enumerate(reader):
        if pular_cabecalho and i == 0:
            continue
        if len(row) <= max(col_data, col_descricao, col_valor):
            continue

        try:
            data_str = row[col_data].strip()
            descricao = row[col_descricao].strip()
            valor_str = row[col_valor].strip().replace(".", "").replace(",", ".")

            data_parsed = datetime.strptime(data_str, formato_data).date()
            valor = float(valor_str)

            linhas.append(
                LinhaExtrato(
                    data=data_parsed,
                    descricao=descricao,
                    valor=valor,
                )
            )
        except (ValueError, IndexError):
            continue

    return linhas


def detectar_formato(nome_arquivo: str) -> str:
    """Detecta o formato do arquivo pelo nome/extensão."""
    nome_lower = nome_arquivo.lower()
    if nome_lower.endswith(".ofx"):
        return "ofx"
    elif nome_lower.endswith(".csv"):
        return "csv"
    else:
        raise ValueError(f"Formato de arquivo não suportado: {nome_arquivo}")
