@echo off
REM Ejecuta Buildozer para Android debug desde el directorio del proyecto.
REM Nota: Buildozer Android debe ejecutarse en Linux/WSL o en un entorno Linux compatible.
cd /d %~dp0
python -m buildozer android debug
pause
