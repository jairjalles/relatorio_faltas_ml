@echo off
setlocal enabledelayedexpansion

:: Caminhos de origem (OneDrive)
set "ORIGEM1=C:\Users\Jair Jales\OneDrive - Top Shop\BASE\DashboardFaltas\FALTAS MERCADO LIVRE 2025.xlsx"
set "ORIGEM2=C:\Users\Jair Jales\OneDrive - Top Shop\BASE\DashboardFaltas\FALTAS MERCADO LIVRE 2025 - Copia.xlsx"

:: Caminho de destino (dentro do repositório)
set "DESTINO=C:\Users\Jair Jales\Documents\Projeto - Relatório de faltas\relatorio_faltas_ml\planilhas"
set "REPO=C:\Users\Jair Jales\Documents\Projeto - Relatório de faltas\relatorio_faltas_ml"

:: ===============================
echo ===============================
echo 🔄 Sincronizando planilhas do OneDrive...
echo ===============================

:: Copia os arquivos
copy "%ORIGEM1%" "%DESTINO%" >nul
copy "%ORIGEM2%" "%DESTINO%" >nul

if %errorlevel% neq 0 (
    echo ❌ Erro ao copiar planilhas!
    pause
    exit /b
)

echo ✅ Planilhas copiadas com sucesso para: %DESTINO%

:: Acessa o repositório
cd /d "%REPO%"

:: Verifica se é um repositório Git
git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo ❌ Esta pasta não é um repositório Git: %REPO%
    pause
    exit /b
)

:: ===============================
echo ===============================
echo 🚀 Enviando para o GitHub...
echo ===============================

git add .
git commit -m "🔄 Atualização automática das planilhas"
git push origin main

if %errorlevel% neq 0 (
    echo ❌ Erro ao enviar para o GitHub!
    pause
    exit /b
)

:: Notificação
echo 🔔 Notificando usuário...
powershell -c "(New-Object Media.SoundPlayer 'C:\Windows\Media\Windows Notify.wav').PlaySync()"
timeout /t 1 >nul
msg * "✅ Projeto sincronizado com sucesso!"

echo ✅ Sincronização concluída com sucesso!
pause
