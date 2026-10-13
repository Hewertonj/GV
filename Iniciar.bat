@echo off
title Gestao de Vendedores
color 1F
cls

echo.
echo  ============================================================
echo   ^>^>  SISTEMA DE GESTAO DE VENDEDORES  ^<^<
echo  ============================================================
echo.
echo  Iniciando servidor, aguarde...
echo.

:: Diretorio do projeto (relativo ao local do .bat)
set "PROJETO=%~dp0"

:: Verifica se Python esta disponivel
python --version >nul 2>&1
if %errorlevel% NEQ 0 (
    echo  [ERRO] Python nao encontrado no PATH.
    echo  Certifique-se de que o Python 3.10 esta instalado.
    pause
    exit /b 1
)

:: Verifica se Streamlit esta instalado
python -m streamlit --version >nul 2>&1
if %errorlevel% NEQ 0 (
    echo  [AVISO] Streamlit nao encontrado. Instalando dependencias...
    pip install -r "%PROJETO%requirements.txt"
    echo.
)

echo  Servidor iniciado! O sistema abrira no navegador automaticamente.
echo  Para encerrar, feche esta janela ou pressione Ctrl+C.
echo.
echo  ============================================================
echo.

:: Inicia o Streamlit apontando para o diretorio do projeto
cd /d "%PROJETO%"
python -m streamlit run app.py --server.headless false --browser.gatherUsageStats false

:: Se o servidor encerrar por erro, exibe mensagem
if %errorlevel% NEQ 0 (
    echo.
    echo  [ERRO] O servidor encerrou inesperadamente ^(codigo %errorlevel%^).
    echo  Verifique os logs acima para mais detalhes.
)

echo.
pause
