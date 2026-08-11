[app]
title = Crypto Certified Switch
package.name = cryptocertifiedswitch
package.domain = com.ccs
source.dir = .
source.include_exts = py,json,txt,md,png,jpg,kv
source.exclude_dirs = .venv,backups,logs,data,tests,__pycache__
version = 7.1.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 35
android.minapi = 26
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = False

[buildozer]
log_level = 2
warn_on_root = 1
