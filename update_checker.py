import urllib.request
import json
import tkinter as tk
from tkinter import messagebox
import threading
import os
import sys
import subprocess

REPO_URL = "https://api.github.com/repos/jacky09299/Languages_Learning/releases/latest"
CURRENT_VERSION = "v1.0.0"

def check_for_updates(app):
    # Only run update check if it's running as a frozen executable (packaged by PyInstaller)
    if not getattr(sys, 'frozen', False):
        print("Not running as frozen executable, skipping update check.")
        return

    def _check():
        try:
            req = urllib.request.Request(REPO_URL, headers={'User-Agent': 'Mozilla/5.0 LanguageLearningApp'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                latest_version = data.get("tag_name", "")
                
                if latest_version and latest_version != CURRENT_VERSION:
                    download_url = None
                    for asset in data.get("assets", []):
                        if asset.get("name") == "Language_Learning.exe":
                            download_url = asset.get("browser_download_url")
                            break
                    
                    if download_url:
                        # Schedule UI update on main thread
                        app.after(1000, lambda: prompt_update(app, latest_version, download_url))
        except Exception as e:
            print(f"Update check failed: {e}")

    threading.Thread(target=_check, daemon=True).start()

def prompt_update(app, latest_version, download_url):
    result = messagebox.askyesno(
        "發現新版本",
        f"目前版本: {CURRENT_VERSION}\n最新版本: {latest_version}\n\n是否要立即下載並更新？\n(更新過程會自動重新啟動應用程式)"
    )
    if result:
        download_and_update(app, download_url)

def download_and_update(app, download_url):
    # Show downloading window
    dl_win = tk.Toplevel(app)
    dl_win.title("更新中")
    dl_win.geometry("300x120")
    dl_win.transient(app)
    dl_win.grab_set()
    tk.Label(dl_win, text="正在下載新版本，請稍候...\n下載完成後程式將自動重啟", justify="center").pack(pady=30)
    app.update()

    def _download():
        try:
            current_exe = sys.executable
            exe_dir = os.path.dirname(current_exe)
            exe_name = os.path.basename(current_exe)
            new_exe_name = "Language_Learning_new.exe"
            new_exe_path = os.path.join(exe_dir, new_exe_name)

            req = urllib.request.Request(download_url, headers={'User-Agent': 'Mozilla/5.0 LanguageLearningApp'})
            with urllib.request.urlopen(req, timeout=60) as response:
                with open(new_exe_path, 'wb') as f:
                    f.write(response.read())
            
            app.after(0, lambda: apply_update(app, exe_dir, exe_name, new_exe_name))
        except Exception as e:
            app.after(0, dl_win.destroy)
            app.after(0, lambda: messagebox.showerror("下載失敗", f"無法下載更新檔案: {e}"))
            
    threading.Thread(target=_download, daemon=True).start()

def apply_update(app, exe_dir, current_exe_name, new_exe_name):
    bat_content = f"""@echo off
setlocal enabledelayedexpansion
timeout /t 2 /nobreak >nul
:wait_process
tasklist | find /i "{current_exe_name}" >nul
if not errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto wait_process
)

set retry=0
:delete_loop
del /f /q "{current_exe_name}"
if exist "{current_exe_name}" (
    set /a retry+=1
    if !retry! lss 10 (
        timeout /t 1 /nobreak >nul
        goto delete_loop
    )
)

ren "{new_exe_name}" "{current_exe_name}"
start "" "{current_exe_name}"
del "%~f0"
"""
    bat_path = os.path.join(exe_dir, "update_app.bat")
    with open(bat_path, "w", encoding="utf-8-sig") as f:
        f.write(bat_content)
    
    app.withdraw()  # Hide main window immediately
    
    # Run the bat in the background
    # CREATE_NO_WINDOW = 0x08000000 to hide the console window of the bat file
    subprocess.Popen(bat_path, shell=True, cwd=exe_dir, creationflags=0x08000000)
    
    if hasattr(app, 'on_closing'):
        app.on_closing()
    else:
        app.destroy()
        sys.exit(0)

def manual_check(app):
    def _check():
        try:
            req = urllib.request.Request(REPO_URL, headers={'User-Agent': 'Mozilla/5.0 LanguageLearningApp'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                latest_version = data.get("tag_name", "")
                
                if latest_version and latest_version != CURRENT_VERSION:
                    download_url = None
                    for asset in data.get("assets", []):
                        if asset.get("name") == "Language_Learning.exe":
                            download_url = asset.get("browser_download_url")
                            break
                    
                    if download_url:
                        app.after(0, lambda: prompt_update(app, latest_version, download_url))
                    else:
                        app.after(0, lambda: messagebox.showinfo("檢查更新", "發現新版本，但尚未上傳安裝檔！"))
                else:
                    app.after(0, lambda: messagebox.showinfo("檢查更新", f"目前已是最新版本 ({CURRENT_VERSION})！"))
        except Exception as e:
            app.after(0, lambda: messagebox.showerror("檢查更新失敗", f"無法連線檢查更新：\n{e}"))

    threading.Thread(target=_check, daemon=True).start()
