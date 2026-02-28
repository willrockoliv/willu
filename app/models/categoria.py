import enum
from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class TipoCategoria(str, enum.Enum):
    RECEITA = "Receita"
    DESPESA = "Despesa"


class NaturezaCategoria(str, enum.Enum):
    FIXA = "Fixa"
    RECORRENTE = "Recorrente"
    VARIAVEL = "Variável"


class Categoria(Base):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo: Mapped[TipoCategoria] = mapped_column(Enum(TipoCategoria), nullable=False)
    natureza: Mapped[NaturezaCategoria] = mapped_column(Enum(NaturezaCategoria), nullable=False)

    transacoes: Mapped[list["Transacao"]] = relationship(  # noqa: F821
        back_populates="categoria"
    )
    dicionarios: Mapped[list["DicionarioConciliacao"]] = relationship(  # noqa: F821
        back_populates="categoria"
    )

    def __repr__(self) -> str:
        return f"<Categoria(id={self.id}, nome='{self.nome}', tipo={self.tipo})>"
