[app]
# Nombre de la aplicación
title = FlexRex
package.name = flexrex
package.domain = org.flexrex
source.dir = .
source.include_exts = py,png,jpg,kv,mp4,json
version = 0.1

# Requisitos limpios y estables
requirements = python3,kivy==2.3.1,kivymd==1.2.0,plyer

orientation = portrait
fullscreen = 0
android.permissions = INTERNET,CAMERA,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
icon.filename = logo_nuevo.png
presplash.filename = logo_nuevo.png

# APIs Estándar
android.archs = arm64-v8a
android.api = 33
android.minapi = 21

# Dejar en blanco para que use la descarga interna controlada por el parche del symlink
android.ndk = 25b
android.accept_sdk_license = True
android.logcat_filters = *:S python:D

[buildozer]
log_level = 2
warn_on_root = 1
