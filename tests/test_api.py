"""Testes automatizados de integração da API HTTP."""
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from http.server import ThreadingHTTPServer

import database
from app import Handler

class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        # A suíte usa SQLite temporário mesmo quando o .env do aluno aponta para MySQL.
        # Assim, os testes não alteram os dados reais do projeto no Workbench.
        database.DB_ENGINE = "sqlite"
        database.DB_PATH = Path(cls.temp.name) / "test.db"
        database.init_db()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(timeout=2); cls.temp.cleanup()

    def request(self, path, method="GET", data=None, expected=200):
        body = None if data is None else json.dumps(data).encode()
        req = Request(self.base + path, data=body, method=method, headers={"Content-Type":"application/json"})
        try:
            with urlopen(req) as response:
                self.assertEqual(response.status, expected)
                return json.loads(response.read().decode())
        except HTTPError as exc:
            self.assertEqual(exc.code, expected)
            return json.loads(exc.read().decode())

    def test_00_frontend_homepage(self):
        with urlopen(self.base + "/") as response:
            self.assertEqual(response.status, 200)
            self.assertIn("Organiza".encode(), response.read())

    def test_01_health(self):
        self.assertEqual(self.request("/api/health")["status"], "ok")

    def test_02_create_category(self):
        category = self.request("/api/categories", "POST", {
            "nome":"Teste Automatizado", "descricao":"Categoria criada pelo teste."
        }, 201)
        self.assertEqual(category["nome"], "Teste Automatizado")

    def test_02_seed_users_and_categories(self):
        self.assertGreaterEqual(len(self.request("/api/users")), 1)
        self.assertGreaterEqual(len(self.request("/api/categories")), 3)

    def test_03_create_task(self):
        user = self.request("/api/users")[0]
        category = self.request("/api/categories")[0]
        task = self.request("/api/tasks", "POST", {
            "titulo":"Teste de integração",
            "descricao":"Registro criado durante teste automatizado.",
            "id_usuario":user["id_usuario"],
            "id_categoria":category["id_categoria"],
            "status":"Pendente","prioridade":"Alta","data_prazo":"2026-12-01"
        }, 201)
        self.assertEqual(task["titulo"], "Teste de integração")
        self.__class__.created_task_id = task["id_tarefa"]

    def test_04_validation_rejects_empty_title(self):
        user = self.request("/api/users")[0]
        result = self.request("/api/tasks", "POST", {"titulo":"x","id_usuario":user["id_usuario"]}, 400)
        self.assertIn("título", result["erro"])

    def test_05_update_status(self):
        tid = getattr(self.__class__, "created_task_id", None)
        self.assertIsNotNone(tid)
        current = next(t for t in self.request("/api/tasks") if t["id_tarefa"] == tid)
        current["status"] = "Concluída"
        updated = self.request(f"/api/tasks/{tid}", "PUT", current)
        self.assertEqual(updated["status"], "Concluída")

    def test_06_filter_by_status(self):
        tasks = self.request("/api/tasks?status=Conclu%C3%ADda")
        self.assertTrue(all(t["status"] == "Concluída" for t in tasks))

    def test_07_summary(self):
        summary = self.request("/api/summary")
        self.assertEqual(summary["total"], summary["pendentes"] + summary["andamento"] + summary["concluidas"])

    def test_08_delete_task(self):
        tid = getattr(self.__class__, "created_task_id", None)
        self.assertIsNotNone(tid)
        result = self.request(f"/api/tasks/{tid}", "DELETE")
        self.assertIn("excluída", result["mensagem"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
