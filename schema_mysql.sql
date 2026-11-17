-- Projeto PIT-II: Gerenciador de Tarefas
-- Dialeto: MySQL 8.0+ / InnoDB / utf8mb4
CREATE DATABASE IF NOT EXISTS gerenciador_tarefas
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE gerenciador_tarefas;

CREATE TABLE usuarios (
  id_usuario INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(100) NOT NULL,
  email VARCHAR(150) NOT NULL UNIQUE,
  criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE categorias (
  id_categoria INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(60) NOT NULL UNIQUE,
  descricao VARCHAR(255) NULL,
  criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE tarefas (
  id_tarefa INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_usuario INT UNSIGNED NOT NULL,
  id_categoria INT UNSIGNED NULL,
  titulo VARCHAR(120) NOT NULL,
  descricao TEXT NULL,
  data_prazo DATE NULL,
  status ENUM('Pendente','Em andamento','Concluída') NOT NULL DEFAULT 'Pendente',
  prioridade ENUM('Baixa','Média','Alta') NOT NULL DEFAULT 'Média',
  criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_tarefa_usuario FOREIGN KEY (id_usuario)
    REFERENCES usuarios(id_usuario) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_tarefa_categoria FOREIGN KEY (id_categoria)
    REFERENCES categorias(id_categoria) ON UPDATE CASCADE ON DELETE SET NULL,
  INDEX idx_tarefas_usuario (id_usuario),
  INDEX idx_tarefas_categoria (id_categoria),
  INDEX idx_tarefas_status (status),
  INDEX idx_tarefas_prazo (data_prazo)
) ENGINE=InnoDB;

INSERT INTO usuarios (nome,email) VALUES ('Usuário Demonstração','demo@local.test');
INSERT INTO categorias (nome,descricao) VALUES
('Estudos','Atividades acadêmicas e estudos'),
('Trabalho','Atividades profissionais'),
('Pessoal','Compromissos pessoais');
INSERT INTO tarefas (id_usuario,id_categoria,titulo,descricao,status,prioridade)
SELECT u.id_usuario,c.id_categoria,'Revisar modelagem de dados','Estudar modelo conceitual, lógico e físico.','Em andamento','Alta'
FROM usuarios u JOIN categorias c ON c.nome='Estudos' WHERE u.email='demo@local.test';
INSERT INTO tarefas (id_usuario,id_categoria,titulo,descricao,status,prioridade)
SELECT u.id_usuario,c.id_categoria,'Finalizar atividade PIT-II','Conferir documentação e executar os testes.','Pendente','Alta'
FROM usuarios u JOIN categorias c ON c.nome='Estudos' WHERE u.email='demo@local.test';
