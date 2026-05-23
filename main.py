from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import Optional
from database import SessionLocal, engine
import models, schemas, crud

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API de Agendamento de Limpeza",
    description="Sistema de agendamento de serviços de limpeza - UNIFECAF",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ───────────── USUÁRIOS ─────────────

@app.post("/usuarios/", response_model=schemas.UsuarioOut, tags=["Usuários"], summary="Cadastrar usuário")
def cadastrar_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    """Cadastra um novo cliente ou profissional."""
    existente = crud.buscar_usuario_por_email(db, usuario.email)
    if existente:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")
    return crud.criar_usuario(db, usuario)


@app.post("/login/", tags=["Usuários"], summary="Login")
def login(dados: schemas.Login, db: Session = Depends(get_db)):
    """Autentica o usuário com e-mail e senha."""
    usuario = crud.autenticar_usuario(db, dados.email, dados.senha)
    if not usuario:
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos.")
    return {"mensagem": "Login realizado com sucesso.", "usuario_id": usuario.id, "perfil": usuario.perfil}


@app.get("/usuarios/{usuario_id}", response_model=schemas.UsuarioOut, tags=["Usuários"], summary="Buscar usuário")
def buscar_usuario(usuario_id: int, db: Session = Depends(get_db)):
    usuario = crud.buscar_usuario_por_id(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return usuario


# ───────────── AGENDAMENTOS ─────────────

@app.post("/agendamentos/", response_model=schemas.AgendamentoOut, tags=["Agendamentos"], summary="Criar agendamento")
def criar_agendamento(agendamento: schemas.AgendamentoCreate, db: Session = Depends(get_db)):
    """
    Cria um novo agendamento de serviço de limpeza.
    - Valida se a data não está no passado.
    - Verifica conflito de horário para o mesmo profissional.
    """
    if agendamento.data_hora <= datetime.now():
        raise HTTPException(status_code=400, detail="A data e horário devem ser no futuro.")

    if not crud.buscar_usuario_por_id(db, agendamento.cliente_id):
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    if not crud.buscar_usuario_por_id(db, agendamento.profissional_id):
        raise HTTPException(status_code=404, detail="Profissional não encontrado.")

    conflito = crud.verificar_conflito(db, agendamento.profissional_id, agendamento.data_hora)
    if conflito:
        raise HTTPException(status_code=409, detail="Horário já ocupado. Escolha outro horário.")

    return crud.criar_agendamento(db, agendamento)


@app.get("/agendamentos/usuario/{usuario_id}", response_model=list[schemas.AgendamentoOut], tags=["Agendamentos"], summary="Listar agendamentos do usuário")
def listar_agendamentos_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """Lista todos os agendamentos de um usuário (cliente ou profissional)."""
    if not crud.buscar_usuario_por_id(db, usuario_id):
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return crud.listar_agendamentos_usuario(db, usuario_id)


@app.get("/agendamentos/usuario/{usuario_id}/agenda", response_model=list[schemas.AgendamentoOut], tags=["Agendamentos"], summary="Consultar agenda por dia ou semana")
def consultar_agenda(
    usuario_id: int,
    modo: str = Query("dia", enum=["dia", "semana"], description="Filtrar por 'dia' ou 'semana'"),
    data: Optional[date] = Query(None, description="Data de referência (YYYY-MM-DD). Padrão: hoje."),
    db: Session = Depends(get_db)
):
    """
    Consulta a agenda de um usuário filtrando por dia ou semana.
    - modo=dia: retorna agendamentos do dia informado (padrão: hoje).
    - modo=semana: retorna agendamentos dos 7 dias a partir da data informada.
    - Se não houver agendamentos, retorna lista vazia sem erro.
    """
    if modo not in ("dia", "semana"):
        raise HTTPException(status_code=422, detail="Modo inválido. Use 'dia' ou 'semana'.")

    if not crud.buscar_usuario_por_id(db, usuario_id):
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    data_ref = data or date.today()
    return crud.consultar_agenda_por_periodo(db, usuario_id, data_ref, modo)


@app.get("/agendamentos/{agendamento_id}", response_model=schemas.AgendamentoOut, tags=["Agendamentos"], summary="Buscar agendamento")
def buscar_agendamento(agendamento_id: int, db: Session = Depends(get_db)):
    ag = crud.buscar_agendamento_por_id(db, agendamento_id)
    if not ag:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")
    return ag


@app.patch("/agendamentos/{agendamento_id}/cancelar", response_model=schemas.AgendamentoOut, tags=["Agendamentos"], summary="Cancelar agendamento")
def cancelar_agendamento(agendamento_id: int, db: Session = Depends(get_db)):
    """Cancela um agendamento existente alterando seu status."""
    ag = crud.buscar_agendamento_por_id(db, agendamento_id)
    if not ag:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")
    if ag.status == "cancelado":
        raise HTTPException(status_code=400, detail="Agendamento já está cancelado.")
    return crud.cancelar_agendamento(db, agendamento_id)


@app.get("/agendamentos/horarios/disponiveis", tags=["Agendamentos"], summary="Listar todos os agendamentos ativos")
def listar_todos_agendamentos(db: Session = Depends(get_db)):
    """Lista todos os agendamentos ativos no sistema."""
    return crud.listar_todos_agendamentos(db)
