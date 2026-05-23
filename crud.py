from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta, date
import models, schemas


# ───────────── USUÁRIOS ─────────────

def criar_usuario(db: Session, usuario: schemas.UsuarioCreate):
    novo = models.Usuario(
        nome=usuario.nome,
        email=usuario.email,
        senha=usuario.senha,
        perfil=usuario.perfil
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


def buscar_usuario_por_email(db: Session, email: str):
    return db.query(models.Usuario).filter(models.Usuario.email == email).first()


def buscar_usuario_por_id(db: Session, usuario_id: int):
    return db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()


def autenticar_usuario(db: Session, email: str, senha: str):
    usuario = buscar_usuario_por_email(db, email)
    if not usuario or usuario.senha != senha:
        return None
    return usuario


# ───────────── AGENDAMENTOS ─────────────

def verificar_conflito(db: Session, profissional_id: int, data_hora: datetime):
    """
    Verifica se o profissional já tem agendamento ativo dentro de uma
    janela de 2 horas ao redor do horário solicitado.
    """
    janela_inicio = data_hora - timedelta(hours=2)
    janela_fim = data_hora + timedelta(hours=2)
    return db.query(models.Agendamento).filter(
        models.Agendamento.profissional_id == profissional_id,
        models.Agendamento.status == models.StatusEnum.ativo,
        models.Agendamento.data_hora >= janela_inicio,
        models.Agendamento.data_hora < janela_fim
    ).first()


def criar_agendamento(db: Session, agendamento: schemas.AgendamentoCreate):
    novo = models.Agendamento(
        cliente_id=agendamento.cliente_id,
        profissional_id=agendamento.profissional_id,
        data_hora=agendamento.data_hora,
        tipo_limpeza=agendamento.tipo_limpeza,
        observacoes=agendamento.observacoes,
        status=models.StatusEnum.ativo
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


def buscar_agendamento_por_id(db: Session, agendamento_id: int):
    return db.query(models.Agendamento).filter(models.Agendamento.id == agendamento_id).first()


def listar_agendamentos_usuario(db: Session, usuario_id: int):
    """Retorna todos os agendamentos onde o usuário é cliente OU profissional."""
    return db.query(models.Agendamento).filter(
        or_(
            models.Agendamento.cliente_id == usuario_id,
            models.Agendamento.profissional_id == usuario_id
        )
    ).all()


def consultar_agenda_por_periodo(db: Session, usuario_id: int, data_ref: date, modo: str):
    """
    Filtra agendamentos do usuário por dia ou semana.
    - modo='dia'   → apenas o dia de data_ref
    - modo='semana'→ os 7 dias a partir de data_ref
    Se não houver resultados, retorna lista vazia (não levanta erro).
    """
    inicio = datetime(data_ref.year, data_ref.month, data_ref.day, 0, 0, 0)
    if modo == "dia":
        fim = datetime(data_ref.year, data_ref.month, data_ref.day, 23, 59, 59)
    else:  # semana
        fim_date = data_ref + timedelta(days=6)
        fim = datetime(fim_date.year, fim_date.month, fim_date.day, 23, 59, 59)

    return db.query(models.Agendamento).filter(
        or_(
            models.Agendamento.cliente_id == usuario_id,
            models.Agendamento.profissional_id == usuario_id
        ),
        models.Agendamento.data_hora >= inicio,
        models.Agendamento.data_hora <= fim
    ).order_by(models.Agendamento.data_hora).all()


def cancelar_agendamento(db: Session, agendamento_id: int):
    ag = buscar_agendamento_por_id(db, agendamento_id)
    ag.status = models.StatusEnum.cancelado
    db.commit()
    db.refresh(ag)
    return ag


def listar_todos_agendamentos(db: Session):
    return db.query(models.Agendamento).filter(
        models.Agendamento.status == models.StatusEnum.ativo
    ).all()
