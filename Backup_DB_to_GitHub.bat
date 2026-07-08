@echo off
chcp 65001 >nul
setlocal

echo ==========================================
echo    資料庫 GitHub 專屬分支備份小工具 
echo ==========================================

:: 1. 檢查檔案與儲存庫大小
:: GitHub 限制：單一檔案嚴格上限為 100MB (104857600 bytes)，整個儲存庫建議保持在 1GB 以下
set FILE_LIMIT=104857600
for %%I in (language_learning.db) do set FILE_SIZE=%%~zI

if %FILE_SIZE% GTR %FILE_LIMIT% (
    echo [錯誤] 您的資料庫檔案大小 (%FILE_SIZE% bytes) 已超過 GitHub 的 100MB 單一檔案上限！
    echo 備份已終止。您必須使用其他方式備份此檔案。
    pause
    exit /b 1
)

set REPO_LIMIT=524288000
for /f "usebackq" %%I in (`powershell -command "(Get-ChildItem -Force -Recurse .git | Measure-Object -Property Length -Sum).Sum"`) do set GIT_SIZE=%%I

if %GIT_SIZE% GTR %REPO_LIMIT% (
    echo [警告] 您的 Git 儲存庫大小 (%GIT_SIZE% bytes) 已超過 500MB 建議上限。
    echo GitHub 雖然允許整個倉庫高達好幾 GB，但過大會影響效能。建議您偶爾留意。
)
echo [1/6] 檔案與儲存庫大小安全，開始備份...

:: 2. 儲存當前分支，並暫存未提交的變更 (確保切換分支不會失敗)
for /f %%I in ('git branch --show-current') do set CURRENT_BRANCH=%%I
echo [2/6] 暫存當前 %CURRENT_BRANCH% 分支的進度...
git stash push -m "Auto-stash before DB backup" >nul

:: 3. 切換到專屬的備份分支 (db-backup)
echo [3/6] 切換到 db-backup 分支...
git checkout db-backup 2>nul
if errorlevel 1 (
    echo 找不到 db-backup 分支，正在建立...
    git checkout -b db-backup
)

:: 4. 複製真實資料庫並強制加入 Git
:: 為什麼要複製？因為如果直接追蹤 language_learning.db，當您切換回 main 時，Git 會把您的真實資料庫刪除！
:: 用一個分身 (github_backup.db) 來給 Git 追蹤，是最安全的做法。
echo [4/6] 建立資料庫分身並提交...
copy /Y language_learning.db github_backup.db >nul
git add -f github_backup.db

for /f "delims=" %%a in ('powershell -command "Get-Date -Format 'yyyy-MM-dd HH:mm:ss'"') do set TIMESTAMP=%%a
git commit -m "Auto-backup DB: %TIMESTAMP%" >nul

:: 5. 推送到 GitHub
echo [5/6] 推送到 GitHub...
git push -u origin db-backup

:: 6. 切回原本的分支並還原工作狀態
echo [6/6] 切換回 %CURRENT_BRANCH% 並還原進度...
git checkout %CURRENT_BRANCH% >nul
:: Git 會自動把 github_backup.db 刪除，讓您的目錄保持乾淨 (真實的 language_learning.db 毫髮無傷)

git stash pop >nul 2>&1

echo ==========================================
echo    備份完成！您的資料庫已安全存入 GitHub！
echo ==========================================
pause
