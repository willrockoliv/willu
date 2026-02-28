from sqlalchemy import String, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Conta(Base):
    __tablename__ = "contas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    saldo_inicial: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)

    transacoes: Mapped[list["Transacao"]] = relationship(  # noqa: F821
        back_populates="conta", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Conta(id={self.id}, nome='{self.nome}')>"
