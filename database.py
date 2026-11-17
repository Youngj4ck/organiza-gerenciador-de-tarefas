"""Camada de persistencia do Organiza: SQLite para testes locais ou MySQL 8+."""
from __future__ import annotations
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("PIT_DB_PATH", BASE_DIR / "gerenciador_tarefas.db"))


def _load_dotenv() -> None:
    """Carrega variáveis simples de um arquivo .env sem dependência extra."""
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


_load_dotenv()
DB_ENGINE = os.environ.get("PIT_DB_ENGINE", "sqlite").strip().lower()

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL CHECK(length(trim(nome)) BETWEEN 2 AND 100),
    email TEXT NOT NULL UNIQUE CHECK(length(trim(email)) <= 150),
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS categorias (
    id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE CHECK(length(trim(nome)) BETWEEN 2 AND 60),
    descricao TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS tarefas (
    id_tarefa INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL,
    id_categoria INTEGER,
    titulo TEXT NOT NULL CHECK(length(trim(titulo)) BETWEEN 3 AND 120),
    descricao TEXT,
    data_prazo TEXT,
    status TEXT NOT NULL DEFAULT 'Pendente'
        CHECK(status IN ('Pendente', 'Em andamento', 'Concluída')),
    prioridade TEXT NOT NULL DEFAULT 'Média'
        CHECK(prioridade IN ('Baixa', 'Média', 'Alta')),
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_tarefa_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_tarefa_categoria FOREIGN KEY (id_categoria)
        REFERENCES categorias(id_categoria) ON UPDATE CASCADE ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_tarefas_usuario ON tarefas(id_usuario);
CREATE INDEX IF NOT EXISTS idx_tarefas_categoria ON tarefas(id_categoria);
CREATE INDEX IF NOT EXISTS idx_tarefas_status ON tarefas(status);
CREATE INDEX IF NOT EXISTS idx_tarefas_prazo ON tarefas(data_prazo);
"""


class _HybridRow(dict):
    """Linha MySQL com acesso por nome ou posição, compatível com o código SQLite."""
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


def _json_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat(sep=" ") if isinstance(value, datetime) else value.isoformat()
    return value


class _MySQLCursorAdapter:
    def __init__(self, cursor):
        self._cursor = cursor

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    def fetchone(self):
        row = self._cursor.fetchone()
        return _HybridRow({k: _json_value(v) for k, v in row.items()}) if row is not None else None

    def fetchall(self):
        return [_HybridRow({k: _json_value(v) for k, v in row.items()}) for row in self._cursor.fetchall()]


class _MySQLConnectionAdapter:
    """Adapta mysql-connector ao subconjunto da API sqlite usado pelo projeto."""
    def __init__(self, connection):
        self._connection = connection

    def execute(self, sql: str, params=()):
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute(sql.replace("?", "%s"), tuple(params or ()))
        return _MySQLCursorAdapter(cursor)

    def executemany(self, sql: str, seq_params):
        cursor = self._connection.cursor(dictionary=True)
        cursor.executemany(sql.replace("?", "%s"), seq_params)
        return _MySQLCursorAdapter(cursor)

    def commit(self):
        self._connection.commit()

    def rollback(self):
        self._connection.rollback()

    def close(self):
        self._connection.close()


def engine_name() -> str:
    return "MySQL" if DB_ENGINE == "mysql" else "SQLite"


def health_check() -> dict[str, str]:
    """Confirma que o mecanismo configurado aceita uma consulta real."""
    with db_session() as con:
        con.execute("SELECT 1").fetchone()
    return {"status": "ok", "database": engine_name()}


def connect():
    if DB_ENGINE == "mysql":
        try:
            import mysql.connector
            from mysql.connector import Error as MySQLError
        except ImportError as exc:
            raise RuntimeError(
                "O driver do MySQL não está instalado. Execute: python -m pip install -r requirements.txt"
            ) from exc

        password = os.environ.get("PIT_MYSQL_PASSWORD", "")
        if not password or password == "COLOQUE_SUA_SENHA_AQUI":
            raise RuntimeError(
                "Configure PIT_MYSQL_PASSWORD no arquivo .env com a senha do usuário MySQL antes de iniciar a aplicação."
            )
        try:
            raw = mysql.connector.connect(
                host=os.environ.get("PIT_MYSQL_HOST", "127.0.0.1"),
                port=int(os.environ.get("PIT_MYSQL_PORT", "3306")),
                database=os.environ.get("PIT_MYSQL_DATABASE", "gerenciador_tarefas"),
                user=os.environ.get("PIT_MYSQL_USER", "root"),
                password=password,
                autocommit=False,
                connection_timeout=8,
            )
            return _MySQLConnectionAdapter(raw)
        except (MySQLError, ValueError) as exc:
            raise RuntimeError(
                "Não foi possível conectar ao MySQL. Confira se o serviço está ligado e se host, porta, banco, usuário e senha no .env estão corretos. "
                f"Detalhe: {exc}"
            ) from exc

    if DB_ENGINE != "sqlite":
        raise RuntimeError("PIT_DB_ENGINE deve ser 'mysql' ou 'sqlite'.")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


@contextmanager
def db_session():
    con = connect()
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db(seed: bool = True) -> None:
    if DB_ENGINE == "mysql":
        # O esquema MySQL é criado pelo script schema_mysql.sql no Workbench.
        # Aqui apenas validamos a conexão e a existência das três tabelas.
        with db_session() as con:
            for table in ("usuarios", "categorias", "tarefas"):
                con.execute(f"SELECT 1 FROM {table} LIMIT 0")
        return

    with db_session() as con:
        con.executescript(SCHEMA)
        if seed:
            if con.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
                con.execute("INSERT INTO usuarios(nome,email) VALUES(?,?)", ("Usuário Demonstração", "demo@local.test"))
            if con.execute("SELECT COUNT(*) FROM categorias").fetchone()[0] == 0:
                con.executemany("INSERT INTO categorias(nome,descricao) VALUES(?,?)", [
                    ("Estudos", "Atividades acadêmicas e estudos"),
                    ("Trabalho", "Atividades profissionais"),
                    ("Pessoal", "Compromissos pessoais"),
                ])
            if con.execute("SELECT COUNT(*) FROM tarefas").fetchone()[0] == 0:
                uid = con.execute("SELECT id_usuario FROM usuarios ORDER BY id_usuario LIMIT 1").fetchone()[0]
                cats = {r["nome"]: r["id_categoria"] for r in con.execute("SELECT id_categoria,nome FROM categorias")}
                con.executemany("""INSERT INTO tarefas
                    (id_usuario,id_categoria,titulo,descricao,data_prazo,status,prioridade)
                    VALUES(?,?,?,?,?,?,?)""", [
                    (uid,cats["Estudos"],"Revisar modelagem de dados","Estudar modelo conceitual, lógico e físico.",None,"Em andamento","Alta"),
                    (uid,cats["Estudos"],"Finalizar atividade PIT-II","Conferir documentação e executar os testes.",None,"Pendente","Alta"),
                    (uid,cats["Pessoal"],"Organizar a semana","Separar horários para estudo e descanso.",None,"Concluída","Baixa"),
                ])


def _rowdict(row) -> dict[str, Any] | None:
    if row is None:
        return None
    result = dict(row)
    return {k: _json_value(v) for k, v in result.items()}


def list_users() -> list[dict[str, Any]]:
    with db_session() as con:
        return [_rowdict(r) for r in con.execute("SELECT id_usuario,nome,email,criado_em FROM usuarios ORDER BY nome").fetchall()]


def create_user(data: dict[str, Any]) -> dict[str, Any]:
    nome = str(data.get("nome", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    if len(nome) < 2 or len(nome) > 100:
        raise ValueError("O nome deve ter entre 2 e 100 caracteres.")
    if "@" not in email or len(email) > 150:
        raise ValueError("Informe um e-mail válido.")
    with db_session() as con:
        cur = con.execute("INSERT INTO usuarios(nome,email) VALUES(?,?)", (nome,email))
        new_id = cur.lastrowid
        return _rowdict(con.execute("SELECT id_usuario,nome,email,criado_em FROM usuarios WHERE id_usuario=?", (new_id,)).fetchone())


def list_categories() -> list[dict[str, Any]]:
    with db_session() as con:
        rows = con.execute("""SELECT c.id_categoria,c.nome,c.descricao,c.criado_em,
            COUNT(t.id_tarefa) AS total_tarefas FROM categorias c
            LEFT JOIN tarefas t ON t.id_categoria=c.id_categoria
            GROUP BY c.id_categoria ORDER BY c.nome""").fetchall()
        return [_rowdict(r) for r in rows]


def create_category(data: dict[str, Any]) -> dict[str, Any]:
    nome = str(data.get("nome", "")).strip()
    descricao = str(data.get("descricao", "")).strip()
    if len(nome) < 2 or len(nome) > 60:
        raise ValueError("O nome da categoria deve ter entre 2 e 60 caracteres.")
    with db_session() as con:
        cur = con.execute("INSERT INTO categorias(nome,descricao) VALUES(?,?)", (nome,descricao or None))
        new_id = cur.lastrowid
        return _rowdict(con.execute("SELECT id_categoria,nome,descricao,criado_em FROM categorias WHERE id_categoria=?", (new_id,)).fetchone())


def list_tasks(filters: dict[str, str] | None = None) -> list[dict[str, Any]]:
    filters = filters or {}
    where, args = [], []
    if filters.get("status") in ("Pendente", "Em andamento", "Concluída"):
        where.append("t.status=?"); args.append(filters["status"])
    if filters.get("categoria"):
        try:
            where.append("t.id_categoria=?"); args.append(int(filters["categoria"]))
        except ValueError:
            pass
    if filters.get("q"):
        q = f"%{filters['q'].strip()}%"
        where.append("(t.titulo LIKE ? OR COALESCE(t.descricao,'') LIKE ?)"); args.extend([q,q])
    sql = """SELECT t.id_tarefa,t.id_usuario,t.id_categoria,t.titulo,t.descricao,t.data_prazo,
        t.status,t.prioridade,t.criado_em,t.atualizado_em,u.nome AS usuario_nome,
        c.nome AS categoria_nome FROM tarefas t
        JOIN usuarios u ON u.id_usuario=t.id_usuario
        LEFT JOIN categorias c ON c.id_categoria=t.id_categoria"""
    if where: sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY CASE t.status WHEN 'Pendente' THEN 1 WHEN 'Em andamento' THEN 2 ELSE 3 END, t.data_prazo IS NULL, t.data_prazo, t.id_tarefa DESC"
    with db_session() as con:
        return [_rowdict(r) for r in con.execute(sql,args).fetchall()]


def get_task(task_id: int) -> dict[str, Any] | None:
    rows = list_tasks()
    return next((r for r in rows if r["id_tarefa"] == task_id), None)


def save_task(data: dict[str, Any], task_id: int | None = None) -> dict[str, Any]:
    title = str(data.get("titulo", "")).strip()
    desc = str(data.get("descricao", "")).strip()
    status = str(data.get("status", "Pendente"))
    priority = str(data.get("prioridade", "Média"))
    due = str(data.get("data_prazo", "")).strip() or None
    try: user_id = int(data.get("id_usuario"))
    except (TypeError, ValueError): raise ValueError("Selecione um usuário responsável.")
    cat_raw = data.get("id_categoria")
    try: category_id = int(cat_raw) if cat_raw not in (None, "", 0, "0") else None
    except (TypeError, ValueError): raise ValueError("Categoria inválida.")
    if len(title) < 3 or len(title) > 120:
        raise ValueError("O título deve ter entre 3 e 120 caracteres.")
    if status not in ("Pendente", "Em andamento", "Concluída"):
        raise ValueError("Status inválido.")
    if priority not in ("Baixa", "Média", "Alta"):
        raise ValueError("Prioridade inválida.")
    if due:
        try: date.fromisoformat(due)
        except ValueError: raise ValueError("A data deve estar no formato AAAA-MM-DD.")
    with db_session() as con:
        if task_id is None:
            cur = con.execute("""INSERT INTO tarefas
                (id_usuario,id_categoria,titulo,descricao,data_prazo,status,prioridade)
                VALUES(?,?,?,?,?,?,?)""", (user_id,category_id,title,desc or None,due,status,priority))
            new_id = cur.lastrowid
        else:
            cur = con.execute("""UPDATE tarefas SET id_usuario=?,id_categoria=?,titulo=?,descricao=?,
                data_prazo=?,status=?,prioridade=?,atualizado_em=CURRENT_TIMESTAMP WHERE id_tarefa=?""",
                (user_id,category_id,title,desc or None,due,status,priority,task_id))
            if cur.rowcount == 0: raise KeyError("Tarefa não encontrada.")
            new_id = task_id
    return get_task(int(new_id))


def delete_task(task_id: int) -> None:
    with db_session() as con:
        cur = con.execute("DELETE FROM tarefas WHERE id_tarefa=?", (task_id,))
        if cur.rowcount == 0: raise KeyError("Tarefa não encontrada.")


def summary() -> dict[str, int]:
    with db_session() as con:
        row = con.execute("""SELECT COUNT(*) total,
            SUM(CASE WHEN status='Pendente' THEN 1 ELSE 0 END) pendentes,
            SUM(CASE WHEN status='Em andamento' THEN 1 ELSE 0 END) andamento,
            SUM(CASE WHEN status='Concluída' THEN 1 ELSE 0 END) concluidas
            FROM tarefas""").fetchone()
        row = _rowdict(row) or {}
        return {k: int(row.get(k) or 0) for k in ("total","pendentes","andamento","concluidas")}
