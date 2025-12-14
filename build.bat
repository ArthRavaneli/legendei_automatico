@echo off
title Criando Gerador de Legendas IA...
color 0A

echo ========================================================
echo          INICIANDO PROCESSO DE BUILD AUTOMATICO
echo ========================================================
echo.

:: 1. Verifica e Ativa o Ambiente Virtual
if exist "venv\Scripts\activate.bat" (
    echo [1/4] Ativando ambiente virtual (venv)...
    call venv\Scripts\activate.bat
) else (
    color 0C
    echo [ERRO] A pasta 'venv' nao foi encontrada!
    echo Certifique-se de que este arquivo esta na mesma pasta do projeto.
    pause
    exit
)

:: 2. Limpa builds anteriores para evitar erros
if exist "dist" (
    echo [2/4] Limpando versoes antigas...
    rmdir /s /q "dist"
    rmdir /s /q "build"
)

:: 3. Roda o PyInstaller usando o arquivo .spec
echo.
echo [3/4] Gerando o executavel (Isso pode demorar um pouco)...
echo --------------------------------------------------------
pyinstaller --clean --noconfirm GeradorLegendasIA.spec

if %errorlevel% neq 0 (
    color 0C
    echo.
    echo [ERRO] Ocorreu um erro ao criar o executavel.
    echo Verifique as mensagens acima.
    pause
    exit
)

:: 4. Copia o FFmpeg (O passo crucial)
echo.
echo --------------------------------------------------------
echo [4/4] Configurando arquivos finais...

if exist "ffmpeg.exe" (
    copy /Y "ffmpeg.exe" "dist\ffmpeg.exe" >nul
    echo [OK] FFmpeg copiado automaticamente para a pasta 'dist'.
) else (
    color 0E
    echo [AVISO] O arquivo 'ffmpeg.exe' nao foi encontrado na raiz!
    echo O programa criado NAO vai funcionar sem ele.
    echo Por favor, coloque o ffmpeg.exe na pasta 'dist' manualmente.
)

echo.
echo ========================================================
echo                 CONCLUIDO COM SUCESSO!
echo ========================================================
echo.
echo O seu programa pronto para uso ou envio esta na pasta:
echo  --^> %CD%\dist
echo.
pause