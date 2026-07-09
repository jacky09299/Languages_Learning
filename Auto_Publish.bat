@echo off
chcp 65001 >nul
setlocal

echo ==========================================
echo       自動發布新版本流程腳本
echo ==========================================

:: 讀取目前的版本號
python -c "import re; print(re.search(r'CURRENT_VERSION\s*=\s*\"(.*?)\"', open('update_checker.py', encoding='utf-8').read()).group(1))" > temp_ver.txt
set /p VERSION=<temp_ver.txt
del temp_ver.txt

echo.
echo 偵測到程式碼中的版號為：%VERSION%
echo.

echo [1/2] 提交版號更動至 Git 並推送標籤 ...
git add update_checker.py
git commit -m "Bump version to %VERSION%"
git tag %VERSION%
git push origin %VERSION%
git push

echo.
echo [2/2] 開啟 GitHub Release 頁面 ...
start https://github.com/jacky09299/Languages_Learning/releases/new?tag=%VERSION%

echo ==========================================
echo.
echo 發布前準備已完成！
echo 請在彈出的網頁中完成最後步驟：
echo 1. 確認標籤 (tag) 為 %VERSION%。
echo 2. 將您用 Build.bat 打包好的 Language_Learning.exe 拖曳上傳至網頁中的 Attach binaries 區塊。
echo 3. 點擊綠色的 "Publish release" 按鈕。
echo.
echo 完成後，舊版軟體的使用者就會在下次打開時收到更新通知了！
echo ==========================================
pause
