# Organiza — Gerenciador de Tarefas | Projeto PIT-II

Protótipo acadêmico de aplicação web para cadastro e acompanhamento de tarefas. A aplicação está preparada para utilizar **MySQL 8.0+ / InnoDB** como banco principal. A suíte de testes automatizados usa SQLite temporário, isolado dos dados reais.

## 1. O que o sistema faz

- Exibe totais de tarefas pendentes, em andamento e concluídas.
- Cadastra, edita e exclui tarefas.
- Registra título, descrição, prazo, status, prioridade, responsável e categoria.
- Filtra tarefas por status e categoria e permite busca por texto.
- Cadastra novos usuários e categorias pela API.
- Mantém os dados em MySQL quando `PIT_DB_ENGINE=mysql` está configurado.

## 2. Requisitos

- Python 3.10 ou superior.
- MySQL Server 8.0+ instalado e em execução.
- Banco `gerenciador_tarefas` com as tabelas `usuarios`, `categorias` e `tarefas` criadas pelo script `schema_mysql.sql`.
- MySQL Connector/Python (instalado pelo `Iniciar_Windows.bat` ou `pip`).
- Navegador atualizado.

## 3. Primeira configuração no Windows

1. Extraia o ZIP para uma pasta local.
2. Abra a pasta `Projeto_PIT_II_Gerenciador_Tarefas`.
3. Execute `Iniciar_Windows.bat`.
4. Na primeira execução, o arquivo `.env` será criado e aberto no Bloco de Notas.
5. Substitua `COLOQUE_SUA_SENHA_AQUI` pela senha do usuário MySQL (normalmente `root`) que você definiu na instalação. Não compartilhe essa senha.
6. Confirme que host, porta e banco estão assim: `127.0.0.1`, `3306` e `gerenciador_tarefas`.
7. Salve e feche o Bloco de Notas. Pressione uma tecla no terminal para continuar.
8. O instalador executará `python -m pip install -r requirements.txt` e iniciará `python app.py`.
9. Abra `http://127.0.0.1:8000` no navegador.

**Importante:** o `.env` contém a senha local e está no `.gitignore`; não o publique no GitHub. O aplicativo não cria o esquema MySQL automaticamente: o banco e as três tabelas devem existir antes da inicialização.

## 4. Confirmar a conexão

Com o servidor web iniciado, abra no navegador `http://127.0.0.1:8000/api/health`. A resposta esperada é semelhante a:

```json
{"status":"ok","database":"MySQL"}
```

Se aparecer `SQLite`, a aplicação não leu o `.env` ou `PIT_DB_ENGINE` não está configurado como `mysql`. Se houver erro de conexão, confira serviço MySQL, senha, porta e nome do banco.

## 5. Configuração manual / Linux / macOS

Copie `.env.example` para `.env`, edite a senha e instale o driver:

```bash
python -m pip install -r requirements.txt
python app.py
```

Depois abra `http://127.0.0.1:8000`. Para encerrar, pressione `Ctrl+C` no terminal.

## 6. Estrutura do projeto

```text
Projeto_PIT_II_Gerenciador_Tarefas/
├── app.py                         # servidor HTTP e controladores da API
├── database.py                    # camada de persistência SQLite/MySQL
├── .env.example                   # exemplo de configuração local (sem senha real)
├── .gitignore                     # impede publicar .env e bases locais
├── requirements.txt               # driver MySQL Connector/Python
├── schema_mysql.sql               # modelo físico para MySQL 8+ / InnoDB
├── schema_sqlite.sql              # esquema usado para testes isolados
├── static/                        # HTML, CSS e JavaScript da interface
├── tests/test_api.py              # dez testes automatizados da API em SQLite temporário
├── diagramas/                     # modelos conceitual e lógico/ER
└── docs/                          # manual, roteiro e relatório preenchido
```

## 7. Modelo de dados

Entidades: `USUARIOS`, `CATEGORIAS` e `TAREFAS`.

- Um usuário pode estar relacionado a zero ou muitas tarefas; cada tarefa pertence obrigatoriamente a um usuário (1:N).
- Uma categoria pode estar relacionada a zero ou muitas tarefas; uma tarefa pode não ter categoria ou pertencer a uma categoria (1:N, participação opcional do lado da tarefa).
- Chaves primárias: `id_usuario`, `id_categoria` e `id_tarefa`.
- Chaves estrangeiras: `tarefas.id_usuario` → `usuarios.id_usuario` e `tarefas.id_categoria` → `categorias.id_categoria`.
- `ON DELETE RESTRICT` impede excluir usuário que possua tarefas; `ON DELETE SET NULL` preserva tarefas quando uma categoria é excluída.

## 8. Banco de dados e script SQL

A persistência principal da aplicação usa MySQL 8.0+ com InnoDB. O arquivo `schema_mysql.sql` cria o banco, as tabelas, restrições, índices e registros iniciais de demonstração. **Não execute o script novamente se já tiver criado essas tabelas e dados no Workbench**, pois as instruções `CREATE TABLE` e os `INSERT` iniciais podem gerar duplicidades/erros.

O arquivo `schema_sqlite.sql` e o modo SQLite são mantidos para a suíte automatizada de testes, sempre em base temporária.

## 9. API disponível

| Método | Rota | Finalidade |
|---|---|---|
| GET | `/api/health` | Verificar servidor e banco ativo |
| GET | `/api/summary` | Obter indicadores do painel |
| GET | `/api/users` | Listar usuários |
| POST | `/api/users` | Cadastrar usuário |
| GET | `/api/categories` | Listar categorias |
| POST | `/api/categories` | Cadastrar categoria |
| GET | `/api/tasks` | Listar tarefas; aceita `status`, `categoria` e `q` |
| POST | `/api/tasks` | Cadastrar tarefa |
| PUT | `/api/tasks/{id}` | Atualizar tarefa |
| DELETE | `/api/tasks/{id}` | Excluir tarefa |

## 10. Testes

Execute na pasta do projeto:

```bash
python -m unittest discover -s tests -v
```

Os testes automatizados usam uma base SQLite temporária e isolada, para não inserir nem excluir registros do banco MySQL do estudante. Eles cobrem a página inicial, saúde da API, cadastro de categoria e tarefa, validação, atualização, filtro, indicadores e exclusão.

Os testes manuais realizados pelo estudante no MySQL Workbench devem ser documentados com capturas de tela (estrutura das tabelas, chaves estrangeiras, inserção/consulta, atualização, filtro e exclusão). Os cinco testes com colegas exigidos pela instituição ainda precisam ser realizados e registrados; não foram simulados nem inventados.

## 11. Limitações e cuidados

- Protótipo acadêmico para execução local. Não possui autenticação, controle de acesso ou criptografia de tráfego.
- Não publicar na internet nem inserir dados pessoais reais sem implementar autenticação, autorização, HTTPS, backups e revisão de segurança.
- `127.0.0.1` é acessível somente no computador onde o servidor está em execução; não é link público.
- GitHub, hospedagem pública e vídeo narrado dependem das contas e ações do estudante. Inserir apenas links reais após publicação.

## 12. Identificação acadêmica

Estudante: Yuri dos Reis Coelho. RGM: 36151980. A documentação original do PIT-I não foi fornecida; o planejamento deste protótipo foi reconstruído para o PIT-II, sem alegar revisão de arquivos anteriores.
