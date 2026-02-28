from pydantic import BaseModel


class ContaCreate(BaseModel):
    nome: str
    saldo_inicial: float = 0.0


class ContaUpdate(BaseModel):
    nome: str | None = None
    saldo_inicial: float | None = None


class ContaRead(BaseModel):
    id: int
    nome: str
    saldo_inicial: float

    model_config = {"from_attributes": True}
