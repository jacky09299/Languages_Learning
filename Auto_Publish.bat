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
echo [2/2] 建立 GitHub Release 並自動上傳檔案 ...
gh release create %VERSION% Release_Package\Language_Learning.exe --title "%VERSION%" --notes "自動發布版本 %VERSION%"

echo ==========================================
echo.
echo 發布已全自動完成！
echo 您已成功建立 Release 並上傳最新安裝檔，使用者將在下次開啟時收到更新通知。
echo ==========================================
pause
