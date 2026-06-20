# ==========================================
# KEEP SECRET VIP
# MAIN.PY - FULL STABLE VERSION
# ==========================================

import os
import json
import time
import base64
import sqlite3
import hashlib

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.utils import platform
from kivy.uix.screenmanager import ScreenManager, Screen

# ==========================================
# ANDROID PATHS (بلڈ کے دوران سیف)
# ==========================================

try:
    from android.permissions import request_permissions, Permission
    from android.storage import app_storage_path
except ImportError:
    # بلڈ/ڈیسک ٹاپ ماحول کے لیے ڈمی
    def request_permissions(*args, **kwargs):
        pass
    Permission = None
    def app_storage_path():
        return "."

if platform == "android":
    DB_FILE = os.path.join(app_storage_path(), "vault.db")
else:
    DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vault.db")

# ==========================================
# PIN VALIDATION
# ==========================================

def is_valid_pin(pin):
    if len(pin) < 8 or not pin.isdigit():
        return False
    if pin == pin[0] * len(pin):
        return False
    sequential = "01234567890123456789"
    if pin in sequential:
        return False
    return True

# ==========================================
# PIN HASHING
# ==========================================

def hash_pin(pin, salt):
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, 300000).hex()

# ==========================================
# KEY GENERATION
# ==========================================

def generate_key(pin, salt):
    return PBKDF2(pin.encode(), salt, dkLen=32, count=300000, hmac_hash_module=SHA256)

# ==========================================
# AES-256 GCM ENCRYPTION
# ==========================================

def encrypt_data(text, pin):
    salt = get_random_bytes(16)
    key = generate_key(pin, salt)
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(text.encode("utf-8"))
    
    data = {
        "ciphertext": base64.b64encode(ciphertext).decode(),
        "salt": base64.b64encode(salt).decode(),
        "nonce": base64.b64encode(cipher.nonce).decode(),
        "tag": base64.b64encode(tag).decode()
    }
    return json.dumps(data)

# ==========================================
# AES-256 GCM DECRYPTION
# ==========================================

def decrypt_data(encrypted_json, pin):
    try:
        data = json.loads(encrypted_json)
        salt = base64.b64decode(data["salt"])
        nonce = base64.b64decode(data["nonce"])
        tag = base64.b64decode(data["tag"])
        ciphertext = base64.b64decode(data["ciphertext"])

        key = generate_key(pin, salt)
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        decrypted = cipher.decrypt_and_verify(ciphertext, tag)
        return decrypted.decode()
    except Exception:
        return None

# ==========================================
# DATABASE INITIALIZATION
# ==========================================

def init_database():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS config(
            id INTEGER PRIMARY KEY,
            pin_hash TEXT,
            pin_salt TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS secrets(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            encrypted_data TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_secret(title, encrypted_data):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("INSERT INTO secrets (title, encrypted_data) VALUES (?,?)", (title, encrypted_data))
    conn.commit()
    conn.close()

def load_secrets():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM secrets ORDER BY id DESC")
    data = cur.fetchall()
    conn.close()
    return data

# ==========================================
# MODERN UI (KIVY KV LANG)
# ==========================================

KV = '''
ScreenManager:
    LoginScreen:
    DashboardScreen:
    SaveScreen:
    ViewScreen:

<LoginScreen>
    name: "login"
    BoxLayout:
        orientation: "vertical"
        padding: 25
        spacing: 15
        Label:
            text: "KEEP SECRET VIP"
            font_size: "28sp"
            bold: True
        Label:
            text: "Military Grade Vault"
            font_size: "16sp"
        TextInput:
            id: pin_input
            hint_text: "Enter PIN"
            password: True
            multiline: False
        Button:
            text: "Unlock Vault"
            on_press: root.login()
        Label:
            id: status_label
            text: "Vault Locked"

<DashboardScreen>
    name: "dashboard"
    on_enter: app.start_timer()
    BoxLayout:
        orientation: "vertical"
        padding: 20
        spacing: 10
        Label:
            text: "Dashboard"
            font_size: "24sp"
            bold: True
        Button:
            text: "Save Secret"
            on_press: root.manager.current = "save"
        Button:
            text: "View Secrets"
            on_press: root.open_view()
        Button:
            text: "Lock Vault"
            on_press: root.lock_vault()

<SaveScreen>
    name: "save"
    on_enter: app.start_timer()
    BoxLayout:
        orientation: "vertical"
        padding: 20
        spacing: 10
        Label:
            text: "Save Secret"
        TextInput:
            id: title_input
            hint_text: "Title"
        TextInput:
            id: secret_input
            hint_text: "Secret Text"
        Button:
            text: "Encrypt & Save"
            on_press: root.save_data()
        Button:
            text: "Back"
            on_press: root.manager.current = "dashboard"

<ViewScreen>
    name: "view"
    on_enter: app.start_timer()
    BoxLayout:
        orientation: "vertical"
        padding: 20
        spacing: 10
        Label:
            text: "Stored Secrets"
        TextInput:
            id: secret_list
            readonly: True
        TextInput:
            id: secret_id
            hint_text: "Secret ID"
        Button:
            text: "Decrypt Secret"
            on_press: root.decrypt_selected()
        TextInput:
            id: output_box
            readonly: True
        Button:
            text: "Back"
            on_press: root.manager.current = "dashboard"
'''

# ==========================================
# SCREEN LOGIC CLASSES
# ==========================================

class LoginScreen(Screen):
    def login(self):
        pin = self.ids.pin_input.text
        if not pin:
            return

        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT pin_hash, pin_salt FROM config WHERE id=1")
        row = cur.fetchone()

        if row is None:
            if not is_valid_pin(pin):
                self.ids.status_label.text = "Weak PIN! Must be 8+ digits."
                conn.close()
                return
            
            salt = get_random_bytes(16)
            cur.execute("INSERT INTO config (id, pin_hash, pin_salt) VALUES (1, ?, ?)", 
                        (hash_pin(pin, salt), salt.hex()))
            conn.commit()
            App.get_running_app().session_pin = pin
            self.manager.current = "dashboard"
        else:
            db_hash = row[0]
            db_salt = bytes.fromhex(row[1])
            if hash_pin(pin, db_salt) == db_hash:
                App.get_running_app().session_pin = pin
                self.manager.current = "dashboard"
            else:
                self.ids.status_label.text = "Wrong PIN"
        conn.close()

class DashboardScreen(Screen):
    def lock_vault(self):
        App.get_running_app().stop_timer()
        App.get_running_app().session_pin = ""
        self.manager.current = "login"

    def open_view(self):
        screen = self.manager.get_screen("view")
        screen.load_all()
        self.manager.current = "view"

class SaveScreen(Screen):
    def save_data(self):
        title = self.ids.title_input.text
        text = self.ids.secret_input.text
        pin = App.get_running_app().session_pin

        if not title or not text:
            return

        encrypted = encrypt_data(text, pin)
        save_secret(title, encrypted)
        
        self.ids.title_input.text = ""
        self.ids.secret_input.text = ""
        self.manager.current = "dashboard"

class ViewScreen(Screen):
    def load_all(self):
        records = load_secrets()
        output = ""
        for row in records:
            output += f"[{row[0]}] {row[1]}\n"
        self.ids.secret_list.text = output

    def decrypt_selected(self):
        App.get_running_app().start_timer()
        secret_id = self.ids.secret_id.text
        if not secret_id:
            return

        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT encrypted_data FROM secrets WHERE id=?", (secret_id,))
        row = cur.fetchone()
        conn.close()

        if row is None:
            self.ids.output_box.text = "Secret Not Found"
            return

        pin = App.get_running_app().session_pin
        result = decrypt_data(row[0], pin)

        if result is None:
            self.ids.output_box.text = "Invalid PIN Or Corrupted Data"
        else:
            self.ids.output_box.text = result

# ==========================================
# MAIN APP CLASS
# ==========================================

class KeepSecretVIPApp(App):
    session_pin = ""
    timeout_event = None

    def build(self):
        init_database()
        if platform == "android":
            try:
                request_permissions([Permission.CAMERA, Permission.VIBRATE])
            except Exception:
                pass
        return Builder.load_string(KV)

    def start_timer(self):
        self.stop_timer()
        if self.session_pin:
            self.timeout_event = Clock.schedule_once(self.auto_lock, 60)

    def stop_timer(self):
        if self.timeout_event:
            Clock.unschedule(self.timeout_event)

    def auto_lock(self, dt):
        try:
            self.session_pin = ""
            if self.root:
                self.root.current = "login"
                login = self.root.get_screen("login")
                login.ids.pin_input.text = ""
                login.ids.status_label.text = "Session Locked due to Inactivity"
        except Exception:
            pass

if __name__ == "__main__":
    KeepSecretVIPApp().run()
