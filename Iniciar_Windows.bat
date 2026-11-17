@echo off
cd /d "%~dp0"
if not exist .env (
  copy .env.example .env >nul
  echo Foi criado o arquivo .env.
  echo Informe nele a senha do usuario root do MySQL e salve.
  notepad .env
  echo.
  echo Depois de salvar o .env, pressione qualquer tecla para continuar.
  pause >nul
)
echo Instalando/verificando o driver Python do MySQL...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo Nao foi possivel instalar o driver. Verifique sua conexao com a internet e o Python.
  pause
  exit /b 1
)
echo Iniciando o Organiza conectado ao MySQL...
python app.py
pause
