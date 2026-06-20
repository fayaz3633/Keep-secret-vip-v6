[app]

title = Keep Secret VIP
package.name = keepsecretvip
package.domain = org.fayaz.wallet

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,db

version = 6.0

requirements = python3,kivy,pycryptodome

orientation = portrait
fullscreen = 0

android.api = 33
android.minapi = 24
android.ndk_api = 21

android.permissions = CAMERA,VIBRATE

android.archs = arm64-v8a

android.accept_sdk_license = True

[buildozer]

log_level = 2
warn_on_root = 0
