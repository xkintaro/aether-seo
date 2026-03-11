@echo off
title Dependency Installer
echo Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
echo Installation complete.
pause
