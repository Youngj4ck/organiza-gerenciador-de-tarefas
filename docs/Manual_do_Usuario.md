# Manual do Usuário — Organiza

## Iniciar

1. Confirme que o MySQL Server está ativo e que o banco `gerenciador_tarefas` possui as tabelas `usuarios`, `categorias` e `tarefas`.
2. Na primeira execução, abra `.env` e informe a senha local do MySQL no campo `PIT_MYSQL_PASSWORD`.
3. Execute `Iniciar_Windows.bat`.
4. Abra `http://127.0.0.1:8000` no navegador.
5. Para encerrar, use `Ctrl+C` no terminal.

## Painel

O painel apresenta totais de tarefas, pendentes, em andamento e concluídas. A lista pode ser filtrada por status e categoria e pesquisada por palavras do título ou da descrição.

## Cadastrar tarefa

Clique em **Nova tarefa**, informe título, responsável, status e prioridade. Descrição, prazo e categoria são opcionais. Clique em salvar.

## Editar e excluir

Use os botões de edição e exclusão no cartão da tarefa. A exclusão solicita confirmação antes de remover o registro.

## Categorias

Use **Gerenciar categorias** para criar categorias. O nome deve ser único.

## Banco de dados

A versão de execução principal utiliza MySQL 8.0+ / InnoDB. O arquivo `.env` guarda a configuração local e não deve ser compartilhado. O teste automatizado usa SQLite temporário isolado para não alterar as informações do MySQL.

## Limitações

A aplicação é um protótipo acadêmico local, sem autenticação nem perfis de acesso. Não utilizar dados pessoais sensíveis e não expor o servidor diretamente à internet.
