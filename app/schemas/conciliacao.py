from datetime import date
from pydantic import BaseModel


class LinhaExtrato(BaseModel):
    """Representa uma linha parseada de um extrato bancário (OFX ou CSV)."""
    data: date
    descricao: str
    valor: float


class SugestaoConciliacao(BaseModel):
    """Sugestão de match entre uma linha do extrato e uma transação existente."""
    linha_extrato: LinhaExtrato
    transacao_id: int | None = None
    transacao_descricao: str | None = None
    categoria_id: int | None = None
    categoria_nome: str | None = None
    score: float = 0.0
    origem: str = ""  # "dicionario", "fuzzy", "palavras_chave", "nova"


class ConfirmacaoConciliacao(BaseModel):
    """Dados enviados pelo frontend para confirmar uma conciliação."""
    linha_extrato: LinhaExtrato
    transacao_id: int | None = None
    categoria_id: int | None = None
    descricao: str
    conta_id: int
    salvar_dicionario: bool = True
