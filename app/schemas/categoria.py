from pydantic import BaseModel
from app.models.categoria import TipoCategoria, NaturezaCategoria


class CategoriaCreate(BaseModel):
    nome: str
    tipo: TipoCategoria
    natureza: NaturezaCategoria


class CategoriaUpdate(BaseModel):
    nome: str | None = None
    tipo: TipoCategoria | None = None
    natureza: NaturezaCategoria | None = None


class CategoriaRead(BaseModel):
    id: int
    nome: str
    tipo: TipoCategoria
    natureza: NaturezaCategoria

    model_config = {"from_attributes": True}
