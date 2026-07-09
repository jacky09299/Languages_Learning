@echo off
chcp 65001 >nul
setlocal

echo ==========================================
echo    Language Learning 軟體一鍵打包腳本
echo ==========================================

echo [1/3] 使用 PyInstaller 打包 EXE (這可能需要幾分鐘的時間)...
if exist app_icon.png (
    echo 發現 app_icon.png，正在自動轉換為 ico 格式...
    python -c "from PIL import Image; img = Image.open('app_icon.png'); img.save('app_icon.ico', format='ICO', sizes=[(256, 256)])"
)
set ICON_CMD=
if exist app_icon.ico set ICON_CMD=--icon=app_icon.ico
pyinstaller --onefile --windowed %ICON_CMD% --add-data "app_icon.png;." --add-data "app_icon.ico;." --name Language_Learning main.py

echo [2/3] 準備發布資料夾...
if exist Release_Package rmdir /s /q Release_Package
mkdir Release_Package

echo [3/3] 複製 EXE 到發布資料夾...
copy /Y dist\Language_Learning.exe Release_Package\ >nul

echo ==========================================
echo    打包完成！已準備好 Release_Package 資料夾
echo ==========================================
pause
