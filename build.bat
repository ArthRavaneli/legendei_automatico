@echo off
:: Adiciona uma pausa logo no inicio para garantir que a janela abra
echo Iniciando...
pause

:: Tenta ativar o venv
call venv\Scripts\activate.bat

:: Se o venv falhar, avisa
if %errorlevel% neq 0 (
    echo ERRO: Nao foi possivel ativar o 'venv'.
    pause
    exit
)

:: Roda o PyInstaller
echo Gerando executavel...
pyinstaller --clean --noconfirm interface_legenda.spec

:: Copia o FFmpeg
echo Copiando FFmpeg...
copy /Y "ffmpeg.exe" "dist\ffmpeg.exe"

echo.
echo ============================
echo CONCLUIDO! VERIFIQUE A PASTA DIST
echo ============================
pause