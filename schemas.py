from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional
from models import PerfilEnum, StatusEnum, TipoLimpezaEnum


# ───────────── USUÁRIO ─────────────

class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    perfil: PerfilEnum

    @field_validator("nome")
    @classmethod
    def nome_nao_vazio(cls, v):
        if not v.strip():
            raise ValueError("Nome não pode ser vazio.")
        return v

    @field_validator("senha")
    @classmethod
    def senha_minima(cls, v):
        if len(v) < 6:
            raise ValueError("Senha deve ter pelo menos 6 caracteres.")
        return v


class UsuarioOut(BaseModel):
    id: int
    nome: str
    email: str
    perfil: PerfilEnum

    model_config = {"from_attributes": True}


class Login(BaseModel):
    email: EmailStr
    senha: str


# ───────────── AGENDAMENTO ─────────────

class AgendamentoCreate(BaseModel):
    cliente_id: int
    profissional_id: int
    data_hora: datetime
    tipo_limpeza: TipoLimpezaEnum
    observacoes: Optional[str] = None


class AgendamentoOut(BaseModel):
    id: int
    cliente_id: int
    profissional_id: int
    data_hora: datetime
    tipo_limpeza: TipoLimpezaEnum
    status: StatusEnum
    observacoes: Optional[str]

    model_config = {"from_attributes": True}
