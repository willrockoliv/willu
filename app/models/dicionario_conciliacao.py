from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class DicionarioConciliacao(Base):
    __tablename__ = "dicionario_conciliacao"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    descricao_banco: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categorias.id"), nullable=False)
    descricao_padrao: Mapped[str | None] = mapped_column(String(255), nullable=True)

    categoria: Mapped["Categoria"] = relationship(back_populates="dicionarios")  # noqa: F821

    def __repr__(self) -> str:
        return f"<DicionarioConciliacao(id={self.id}, desc_banco='{self.descricao_banco}')>"
