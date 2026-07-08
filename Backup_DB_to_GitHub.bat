@echo off
chcp 65001 >nul
setlocal

echo ==========================================
echo    Database Only Backup to GitHub
echo ==========================================

REM Check file size limit 100MB
set FILE_LIMIT=104857600
for %%I in (language_learning.db) do set FILE_SIZE=%%~zI

if %FILE_SIZE% GTR %FILE_LIMIT% (
    echo [ERROR] DB file is larger than 100MB GitHub limit!
    pause
    exit /b 1
)
echo [1/4] Size check passed...

REM Get remote URL
for /f "usebackq tokens=*" %%I in (`git config --get remote.origin.url`) do set REPO_URL=%%I

REM Create independent git repo
if not exist .db_backup (
    echo [2/4] Initializing isolated backup repo...
    mkdir .db_backup
    cd .db_backup
    git init >nul
    git remote add origin %REPO_URL%
    cd ..
) else (
    echo [2/4] Isolated backup repo ready...
)

REM Copy and commit
echo [3/4] Copying database...
copy /Y language_learning.db .db_backup\language_learning.db >nul

cd .db_backup
git add language_learning.db

for /f "delims=" %%a in ('powershell -command "Get-Date -Format 'yyyy-MM-dd HH:mm:ss'"') do set TIMESTAMP=%%a
git commit -m "Auto-backup DB: %TIMESTAMP%" >nul

REM Push to remote
echo [4/4] Pushing to GitHub z-backup-db branch...
git push origin HEAD:z-backup-db -f

cd ..
echo ==========================================
echo    Backup Completed Successfully!
echo ==========================================
pause
