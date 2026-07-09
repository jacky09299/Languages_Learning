@echo off
chcp 65001 >nul
setlocal

echo ==========================================
echo       自動發布新版本流程腳本
echo ==========================================
echo.
set /p VERSION=請輸入新版本號 (例如 v1.0.1): 

if "%VERSION%"=="" (
    echo 錯誤：未輸入版本號！
    pause
    exit /b 1
)

echo.
echo [1/4] 更新 update_checker.py 中的版本號為 %VERSION% ...
python -c "import re, sys; f=open('update_checker.py','r',encoding='utf-8'); c=f.read(); f.close(); c=re.sub(r'CURRENT_VERSION\s*=\s*\".*?\"', f'CURRENT_VERSION = \"{sys.argv[1]}\"', c); f=open('update_checker.py','w',encoding='utf-8'); f.write(c); f.close()" %VERSION%

echo.
echo [2/4] 開始呼叫打包腳本 ...
call Build_Release.bat

echo.
echo [3/4] 提交版號更動至 Git 並推送標籤 ...
git add update_checker.py
git commit -m "Bump version to %VERSION%"
git tag %VERSION%
git push origin %VERSION%
git push

echo.
echo [4/4] 開啟 GitHub Release 頁面 ...
start https://github.com/jacky09299/Languages_Learning/releases/new?tag=%VERSION%

echo ==========================================
echo.
echo 發布前準備已完成！
echo 請在彈出的網頁中完成最後步驟：
echo 1. 確認標籤 (tag) 為 %VERSION%。
echo 2. 將 Release_Package 資料夾內的 Language_Learning.exe 拖曳上傳至網頁中的 Attach binaries 區塊。
echo 3. 點擊綠色的 "Publish release" 按鈕。
echo.
echo 完成後，舊版軟體的使用者就會在下次打開時收到更新通知了！
echo ==========================================
pause
