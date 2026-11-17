"""Servidor HTTP e controladores da aplicacao, usando apenas a biblioteca padrao."""
from __future__ import annotations
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import database

BASE = Path(__file__).resolve().parent
STATIC = BASE / "static"

class Handler(BaseHTTPRequestHandler):
    server_version = "PITII-Tarefas/1.0"
    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers(); self.wfile.write(body)

    def read_json(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 100_000: raise ValueError("Requisição muito grande.")
            raw = self.rfile.read(length) if length else b"{}"
            value = json.loads(raw.decode("utf-8"))
            if not isinstance(value, dict): raise ValueError("Envie um objeto JSON.")
            return value
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ValueError("JSON inválido.")

    def do_GET(self):
        parsed = urlparse(self.path); path = parsed.path
        try:
            if path == "/api/health": return self.send_json(database.health_check())
            if path == "/api/summary": return self.send_json(database.summary())
            if path == "/api/users": return self.send_json(database.list_users())
            if path == "/api/categories": return self.send_json(database.list_categories())
            if path == "/api/tasks":
                q = parse_qs(parsed.query)
                filters = {k: (v[0] if v else "") for k,v in q.items()}
                return self.send_json(database.list_tasks(filters))
            if path == "/" or path == "/index.html":
                return self.send_file(STATIC / "index.html")
            if path.startswith("/static/"):
                safe = (STATIC / path.removeprefix("/static/")).resolve()
                if STATIC.resolve() not in safe.parents: return self.send_json({"erro":"Caminho inválido."},400)
                return self.send_file(safe)
            return self.send_json({"erro":"Rota não encontrada."},404)
        except Exception as exc:
            return self.send_json({"erro":str(exc)},500)

    def send_file(self, path: Path):
        if not path.is_file(): return self.send_json({"erro":"Arquivo não encontrado."},404)
        data = path.read_bytes(); content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in ("application/javascript",): content_type += "; charset=utf-8"
        self.send_response(200); self.send_header("Content-Type",content_type); self.send_header("Content-Length",str(len(data)))
        self.end_headers(); self.wfile.write(data)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            data = self.read_json()
            if path == "/api/tasks": return self.send_json(database.save_task(data),201)
            if path == "/api/categories": return self.send_json(database.create_category(data),201)
            if path == "/api/users": return self.send_json(database.create_user(data),201)
            return self.send_json({"erro":"Rota não encontrada."},404)
        except ValueError as exc: return self.send_json({"erro":str(exc)},400)
        except Exception as exc:
            msg = str(exc)
            if "UNIQUE constraint failed" in msg or "Duplicate entry" in msg: msg = "Já existe um cadastro com esse nome ou e-mail."
            if "FOREIGN KEY constraint failed" in msg or "foreign key constraint fails" in msg.lower(): msg = "Usuário ou categoria selecionados não existem."
            return self.send_json({"erro":msg},400)

    def do_PUT(self):
        path = urlparse(self.path).path
        if not path.startswith("/api/tasks/"): return self.send_json({"erro":"Rota não encontrada."},404)
        try:
            task_id = int(path.rsplit("/",1)[1]); data = self.read_json()
            return self.send_json(database.save_task(data,task_id))
        except ValueError as exc: return self.send_json({"erro":str(exc)},400)
        except KeyError as exc: return self.send_json({"erro":str(exc)},404)
        except Exception as exc: return self.send_json({"erro":str(exc)},400)

    def do_DELETE(self):
        path = urlparse(self.path).path
        if not path.startswith("/api/tasks/"): return self.send_json({"erro":"Rota não encontrada."},404)
        try:
            task_id = int(path.rsplit("/",1)[1]); database.delete_task(task_id)
            return self.send_json({"mensagem":"Tarefa excluída."})
        except ValueError: return self.send_json({"erro":"Identificador inválido."},400)
        except KeyError as exc: return self.send_json({"erro":str(exc)},404)

class ReusableServer(ThreadingHTTPServer):
    allow_reuse_address = True

def run_server(host="127.0.0.1", port=8000):
    database.init_db()
    server = ReusableServer((host,port),Handler)
    print(f"Gerenciador de Tarefas disponível em http://{host}:{server.server_port}")
    print("Pressione Ctrl+C para encerrar.")
    try: server.serve_forever()
    except KeyboardInterrupt: print("\nServidor encerrado.")
    finally: server.server_close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Gerenciador de Tarefas - PIT II")
    parser.add_argument("--host",default="127.0.0.1"); parser.add_argument("--port",type=int,default=8000)
    args = parser.parse_args(); run_server(args.host,args.port)
