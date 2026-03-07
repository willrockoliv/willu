from datetime import date
from pydantic import BaseModel
from app.models.transacao import StatusTransacao


class TransacaoCreate(BaseModel):
    conta_id: int
    categoria_id: int | None = None
    valor_previsto: float
    valor_realizado: float | None = None
    data_vencimento: date
    data_pagamento: date | None = None
    status: StatusTransacao = StatusTransacao.PROJETADA
    descricao: str
    descricao_banco: str | None = None
    parcela_atual: int | None = None
    total_parcelas: int | None = None


class TransacaoUpdate(BaseModel):
    conta_id: int | None = None
    categoria_id: int | None = None
    valor_previsto: float | None = None
    valor_realizado: float | None = None
    data_vencimento: date | None = None
    data_pagamento: date | None = None
    status: StatusTransacao | None = None
    descricao: str | None = None
    descricao_banco: str | None = None
    parcela_atual: int | None = None
    total_parcelas: int | None = None


class TransacaoRead(BaseModel):
    id: int
    conta_id: int
    categoria_id: int | None
    valor_previsto: float
    valor_realizado: float | None
    data_vencimento: date
    data_pagamento: date | None
    status: StatusTransacao
    descricao: str
    descricao_banco: str | None
    parcela_atual: int | None = None
    total_parcelas: int | None = None

    model_config = {"from_attributes": True}
