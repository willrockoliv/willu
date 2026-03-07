import enum
from datetime import date
from sqlalchemy import String, Numeric, Enum, ForeignKey, Date, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class StatusTransacao(str, enum.Enum):
    PROJETADA = "Projetada"
    EXECUTADA = "Executada"


class Transacao(Base):
    __tablename__ = "transacoes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conta_id: Mapped[int] = mapped_column(ForeignKey("contas.id"), nullable=False)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categorias.id"), nullable=True)
    valor_previsto: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    valor_realizado: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    data_vencimento: Mapped[date] = mapped_column(Date, nullable=False)
    data_pagamento: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[StatusTransacao] = mapped_column(
        Enum(StatusTransacao, values_callable=lambda x: [e.value for e in x]),
        default=StatusTransacao.PROJETADA, nullable=False
    )
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    descricao_banco: Mapped[str | None] = mapped_column(Text, nullable=True)
    parcela_atual: Mapped[int | None] = mapped_column(nullable=True)
    total_parcelas: Mapped[int | None] = mapped_column(nullable=True)

    conta: Mapped["Conta"] = relationship(back_populates="transacoes")  # noqa: F821
    categoria: Mapped["Categoria"] = relationship(back_populates="transacoes")  # noqa: F821

    @property
    def valor_efetivo(self) -> float:
        """Retorna o valor realizado se executada, senão o previsto."""
        if self.status == StatusTransacao.EXECUTADA and self.valor_realizado is not None:
            return float(self.valor_realizado)
        return float(self.valor_previsto)

    def __repr__(self) -> str:
        return f"<Transacao(id={self.id}, desc='{self.descricao}', status={self.status})>"
