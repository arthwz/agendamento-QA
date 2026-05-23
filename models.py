from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import enum


class PerfilEnum(str, enum.Enum):
    cliente = "cliente"
    profissional = "profissional"


class StatusEnum(str, enum.Enum):
    ativo = "ativo"
    cancelado = "cancelado"


class TipoLimpezaEnum(str, enum.Enum):
    residencial = "residencial"
    comercial = "comercial"
    pos_obra = "pos_obra"
    vidros = "vidros"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    senha = Column(String, nullable=False)
    perfil = Column(Enum(PerfilEnum), nullable=False)

    # Relacionamentos
    agendamentos_como_cliente = relationship(
        "Agendamento", foreign_keys="Agendamento.cliente_id", back_populates="cliente"
    )
    agendamentos_como_profissional = relationship(
        "Agendamento", foreign_keys="Agendamento.profissional_id", back_populates="profissional"
    )


class Agendamento(Base):
    __tablename__ = "agendamentos"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    profissional_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    data_hora = Column(DateTime, nullable=False)
    tipo_limpeza = Column(Enum(TipoLimpezaEnum), nullable=False)
    status = Column(Enum(StatusEnum), default=StatusEnum.ativo, nullable=False)
    observacoes = Column(String, nullable=True)

    # Relacionamentos
    cliente = relationship("Usuario", foreign_keys=[cliente_id], back_populates="agendamentos_como_cliente")
    profissional = relationship("Usuario", foreign_keys=[profissional_id], back_populates="agendamentos_como_profissional")
