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
  status TEXT NOT NULL DEFAULT 'Pendente' CHECK(status IN ('Pendente','Em andamento','Concluída')),
  prioridade TEXT NOT NULL DEFAULT 'Média' CHECK(prioridade IN ('Baixa','Média','Alta')),
  criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON UPDATE CASCADE ON DELETE RESTRICT,
  FOREIGN KEY (id_categoria) REFERENCES categorias(id_categoria) ON UPDATE CASCADE ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_tarefas_usuario ON tarefas(id_usuario);
CREATE INDEX IF NOT EXISTS idx_tarefas_categoria ON tarefas(id_categoria);
CREATE INDEX IF NOT EXISTS idx_tarefas_status ON tarefas(status);
CREATE INDEX IF NOT EXISTS idx_tarefas_prazo ON tarefas(data_prazo);
