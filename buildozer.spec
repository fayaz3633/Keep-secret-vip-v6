[app]

title = Keep Secret VIP
package.name = keepsecretvip
package.domain = org.fayaz

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db

version = 1.0

requirements = python3,kivy,pycryptodome

orientation = portrait
fullscreen = 1

android.api = 35
android.minapi = 24
android.ndk = 28c
android.sdk = 30
android.archs = arm64-v8a

android.permissions = CAMERA, VIBRATE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

android.allow_backup = True
android.debug = True

log_level = 2

android.gradle_dependencies = 
android.add_src = 
android.add_activity = 
android.add_meta_data = 
android.used_permissions = CAMERA, VIBRATE

android.accept_sdk_license = True
android.ndk_license_accept = True
