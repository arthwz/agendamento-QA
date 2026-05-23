# 🧹 API de Agendamento de Limpeza
**UNIFECAF — Prof. Rodrigo Moreira**

Sistema de agendamento de serviços de limpeza desenvolvido com **FastAPI + SQLite**.

---

## 📁 Estrutura do Projeto

```
limpeza_api/
├── main.py              # Rotas da API (endpoints)
├── models.py            # Tabelas do banco de dados (SQLAlchemy)
├── schemas.py           # Validação de dados (Pydantic)
├── crud.py              # Operações no banco (Create, Read, Update, Delete)
├── database.py          # Configuração do banco SQLite
├── test_agendamentos.py # Testes automatizados (pytest)
└── requirements.txt     # Dependências do projeto
```

---

## ⚙️ Como Rodar

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Iniciar a API
```bash
uvicorn main:app --reload
```

### 3. Acessar a documentação interativa
Abra no navegador:
```
http://127.0.0.1:8000/docs
```

### 4. Rodar os testes
```bash
pytest test_agendamentos.py -v
```

---

## 🔗 Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/usuarios/` | Cadastrar novo usuário |
| POST | `/login/` | Autenticar usuário |
| GET | `/usuarios/{id}` | Buscar usuário por ID |
| POST | `/agendamentos/` | Criar agendamento |
| GET | `/agendamentos/usuario/{id}` | Listar agendamentos do usuário |
| GET | `/agendamentos/{id}` | Buscar agendamento por ID |
| PATCH | `/agendamentos/{id}/cancelar` | Cancelar agendamento |
| GET | `/agendamentos/horarios/disponiveis` | Listar todos os agendamentos ativos |

---

## 🧪 Cenários de Teste

| # | Cenário | Comportamento Esperado |
|---|---------|------------------------|
| 1 | Login com senha incorreta | HTTP 401 — acesso bloqueado |
| 2 | Cadastro com e-mail duplicado | HTTP 400 — cadastro impedido |
| 3 | Agendar em horário ocupado | HTTP 409 — horário indisponível |
| 4 | Agendar com data no passado | HTTP 400 — data rejeitada |
| 5 | Consultar agenda sem agendamentos | HTTP 200 — lista vazia `[]` |
| 6 | Cancelar agendamento já cancelado | HTTP 400 — operação rejeitada |
| 7 | Listagem geral de agendamentos | HTTP 200 — lista retornada |

---

## 🗄️ Tipos de Limpeza Disponíveis

- `residencial`
- `comercial`
- `pos_obra`
- `vidros`

## 👤 Perfis de Usuário

- `cliente`
- `profissional`
