[app]
# Nombre de la aplicación
title = FlexRex
package.name = flexrex
package.domain = org.flexrex
source.dir = .
source.include_exts = py,png,jpg,kv,mp4,json
version = 0.1
requirements = python3,kivy==2.3.1,kivymd==1.2.0,ffpyplayer,plyer
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,CAMERA,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
icon.filename = logo_nuevo.png
presplash.filename = logo_nuevo.png

# Configuración de Android
android.archs = arm64-v8a
android.api = 33
android.minapi = 21
android.ndk = 25b
android.logcat_filters = *:S python:D
android.accept_sdk_license = True

# Empaquetado Android
# Buildozer Android debe ejecutarse en Linux/WSL o en un entorno Linux compatible.
# Desde Windows, no hay soporte directo de Buildozer para Android.

[buildozer]
log_level = 2
warn_on_root = 1

[appx]
# Ajustes opcionales para empaquetado adicional
