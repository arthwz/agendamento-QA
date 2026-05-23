"""
Testes de QA — Sistema de Agendamento de Limpeza
UNIFECAF — Prof. Rodrigo Moreira

Rodando: pytest test_agendamentos.py -v
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from main import app, get_db

# ── Banco de dados em memória para testes (não afeta o banco real) ──
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_temp.db"
engine_test = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

Base.metadata.create_all(bind=engine_test)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


# ── Helpers ──────────────────────────────────────────────────────────

def uid():
    """Gera um e-mail único para evitar conflitos entre testes."""
    return str(uuid.uuid4())[:8]

def criar_cliente(email=None, nome="João Silva"):
    email = email or f"cliente_{uid()}@email.com"
    return client.post("/usuarios/", json={
        "nome": nome, "email": email, "senha": "senha123", "perfil": "cliente"
    })

def criar_profissional(email=None, nome="Maria Limpeza"):
    email = email or f"pro_{uid()}@email.com"
    return client.post("/usuarios/", json={
        "nome": nome, "email": email, "senha": "senha123", "perfil": "profissional"
    })

def agendar(cliente_id, profissional_id, data_hora="2099-06-15T10:00:00", tipo="residencial"):
    return client.post("/agendamentos/", json={
        "cliente_id": cliente_id,
        "profissional_id": profissional_id,
        "data_hora": data_hora,
        "tipo_limpeza": tipo
    })


# ════════════════════════════════════════════════════════════════════
# CENÁRIO 1 — Login com senha incorreta
# O que testa: autenticação com credenciais inválidas
# Esperado: HTTP 401 — acesso negado
# ════════════════════════════════════════════════════════════════════

class TestLogin:

    def test_login_senha_incorreta_retorna_401(self):
        criar_cliente("login_errado@email.com")
        resp = client.post("/login/", json={"email": "login_errado@email.com", "senha": "ERRADA"})
        assert resp.status_code == 401
        assert "inválidos" in resp.json()["detail"].lower()

    def test_login_email_inexistente_retorna_401(self):
        resp = client.post("/login/", json={"email": "fantasma@email.com", "senha": "qualquer"})
        assert resp.status_code == 401

    def test_login_correto_retorna_200(self):
        criar_cliente("login_ok@email.com")
        resp = client.post("/login/", json={"email": "login_ok@email.com", "senha": "senha123"})
        assert resp.status_code == 200
        assert "usuario_id" in resp.json()


# ════════════════════════════════════════════════════════════════════
# CENÁRIO 2 — Cadastro com e-mail duplicado
# O que testa: regra de unicidade de e-mail no cadastro
# Esperado: HTTP 400 — cadastro bloqueado com mensagem clara
# ════════════════════════════════════════════════════════════════════

class TestCadastro:

    def test_email_duplicado_retorna_400(self):
        criar_cliente("duplicado@email.com")
        resp = criar_cliente("duplicado@email.com")   # segundo cadastro com mesmo e-mail
        assert resp.status_code == 400
        assert "e-mail" in resp.json()["detail"].lower()

    def test_senha_curta_retorna_422(self):
        resp = client.post("/usuarios/", json={
            "nome": "Teste", "email": "curta@email.com", "senha": "123", "perfil": "cliente"
        })
        assert resp.status_code == 422  # erro de validação Pydantic

    def test_cadastro_valido_retorna_201_ou_200(self):
        resp = client.post("/usuarios/", json={
            "nome": "Novo User", "email": "novo@email.com", "senha": "senha123", "perfil": "cliente"
        })
        assert resp.status_code in (200, 201)
        assert resp.json()["email"] == "novo@email.com"


# ════════════════════════════════════════════════════════════════════
# CENÁRIO 3 — Agendar em horário já ocupado
# O que testa: prevenção de conflito de agenda do profissional
# Esperado: HTTP 409 — horário indisponível
# ════════════════════════════════════════════════════════════════════

class TestConflito:

    def setup_method(self):
        self.cli = criar_cliente().json()["id"]
        self.pro = criar_profissional().json()["id"]

    def test_horario_conflitante_retorna_409(self):
        agendar(self.cli, self.pro, "2099-07-10T09:00:00")
        # Tenta agendar dentro da janela de 2h do mesmo profissional
        resp = agendar(self.cli, self.pro, "2099-07-10T09:30:00")
        assert resp.status_code == 409
        assert "ocupado" in resp.json()["detail"].lower()

    def test_horario_diferente_mesmo_profissional_ok(self):
        agendar(self.cli, self.pro, "2099-07-20T08:00:00")
        # Horário fora da janela de conflito (>2h depois)
        resp = agendar(self.cli, self.pro, "2099-07-20T14:00:00")
        assert resp.status_code == 200


# ════════════════════════════════════════════════════════════════════
# CENÁRIO 4 — Agendamento com data no passado
# O que testa: validação temporal ao criar agendamento
# Esperado: HTTP 400 — data passada rejeitada
# ════════════════════════════════════════════════════════════════════

class TestDataPassada:

    def setup_method(self):
        self.cli = criar_cliente().json()["id"]
        self.pro = criar_profissional().json()["id"]

    def test_data_passada_retorna_400(self):
        resp = agendar(self.cli, self.pro, "2000-01-01T10:00:00")
        assert resp.status_code == 400
        assert "futuro" in resp.json()["detail"].lower()

    def test_data_presente_retorna_400(self):
        # Data de hoje (já passou por microsegundos)
        resp = agendar(self.cli, self.pro, "2024-01-01T00:00:00")
        assert resp.status_code == 400


# ════════════════════════════════════════════════════════════════════
# CENÁRIO 5 — Consulta de agenda sem agendamentos
# O que testa: retorno limpo quando não há registros
# Esperado: lista vazia [], sem erro 500
# ════════════════════════════════════════════════════════════════════

class TestAgendaVazia:

    def test_usuario_sem_agendamentos_retorna_lista_vazia(self):
        resp = criar_cliente("vazio@email.com")
        uid = resp.json()["id"]
        result = client.get(f"/agendamentos/usuario/{uid}")
        assert result.status_code == 200
        assert result.json() == []  # lista vazia, não erro

    def test_usuario_inexistente_retorna_404(self):
        result = client.get("/agendamentos/usuario/99999")
        assert result.status_code == 404


# ════════════════════════════════════════════════════════════════════
# CENÁRIO 6 — Cancelamento de agendamento
# O que testa: fluxo de cancelamento e tentativa de cancelar novamente
# Esperado: status muda para "cancelado"; segunda tentativa retorna 400
# ════════════════════════════════════════════════════════════════════

class TestCancelamento:

    def setup_method(self):
        self.cli = criar_cliente().json()["id"]
        self.pro = criar_profissional().json()["id"]
        ag = agendar(self.cli, self.pro, "2099-08-15T10:00:00")
        self.ag_id = ag.json()["id"]

    def test_cancelar_agendamento_ativo(self):
        resp = client.patch(f"/agendamentos/{self.ag_id}/cancelar")
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelado"

    def test_cancelar_agendamento_ja_cancelado_retorna_400(self):
        client.patch(f"/agendamentos/{self.ag_id}/cancelar")
        resp = client.patch(f"/agendamentos/{self.ag_id}/cancelar")
        assert resp.status_code == 400

    def test_cancelar_agendamento_inexistente_retorna_404(self):
        resp = client.patch("/agendamentos/99999/cancelar")
        assert resp.status_code == 404


# ════════════════════════════════════════════════════════════════════
# CENÁRIO 7 — Listagem geral de horários agendados
# O que testa: endpoint que mostra todos os agendamentos ativos
# Esperado: retorna lista (pode ser vazia) sem erro
# ════════════════════════════════════════════════════════════════════

class TestListagem:

    def test_listagem_retorna_200(self):
        resp = client.get("/agendamentos/horarios/disponiveis")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ════════════════════════════════════════════════════════════════════
# CENÁRIO 8 — Consulta de agenda por dia e por semana
# O que testa: filtro temporal do novo endpoint /agenda
# Esperado: retorna apenas agendamentos do período solicitado
# ════════════════════════════════════════════════════════════════════

class TestAgendaPeriodo:

    def setup_method(self):
        self.cli = criar_cliente().json()["id"]
        self.pro = criar_profissional().json()["id"]
        # Cria agendamento em datas distintas no futuro
        agendar(self.cli, self.pro, "2099-09-01T10:00:00")  # segunda
        agendar(self.cli, self.pro, "2099-09-05T14:00:00")  # sexta (mesma semana)
        agendar(self.cli, self.pro, "2099-09-15T09:00:00")  # semana diferente

    def test_filtro_dia_retorna_apenas_agendamentos_do_dia(self):
        resp = client.get(f"/agendamentos/usuario/{self.cli}/agenda?modo=dia&data=2099-09-01")
        assert resp.status_code == 200
        resultados = resp.json()
        assert len(resultados) == 1
        assert "2099-09-01" in resultados[0]["data_hora"]

    def test_filtro_semana_retorna_agendamentos_da_semana(self):
        resp = client.get(f"/agendamentos/usuario/{self.cli}/agenda?modo=semana&data=2099-09-01")
        assert resp.status_code == 200
        resultados = resp.json()
        # Deve incluir dia 01 e dia 05, mas não dia 15
        assert len(resultados) == 2

    def test_filtro_dia_sem_agendamentos_retorna_lista_vazia(self):
        resp = client.get(f"/agendamentos/usuario/{self.cli}/agenda?modo=dia&data=2099-12-25")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_filtro_usuario_inexistente_retorna_404(self):
        resp = client.get("/agendamentos/usuario/99999/agenda?modo=dia")
        assert resp.status_code == 404

    def test_modo_invalido_retorna_422(self):
        resp = client.get(f"/agendamentos/usuario/{self.cli}/agenda?modo=mes")
        assert resp.status_code == 422
