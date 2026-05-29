@echo off
:: Solicitar permisos de administrador automáticamente para crear el enlace virtual
set "params=%*"
cd /d "%~dp0" && ( if "%USERPROFILE%"=="%DEFAULTUSERPROFILE%" ( set _ADMIN_=1 ) ) || ( echo Subiendo privilegios... )
fsutil dirty query %systemdrive% >nul 2>&1 || (  echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs" && echo UAC.ShellExecute "cmd.exe", "/c ""%~s0"" %params%", "", "runas", 1 >> "%temp%\getadmin.vbs" && "%temp%\getadmin.vbs" && del "%temp%\getadmin.vbs" && exit /B )

title Lanzador Clinident Nativo
cls

echo =======================================================
echo     CONFIGURANDO ENLACE VIRTUAL CON XAMPP (HTDOCS)
echo =======================================================
echo.

:: Detectar la ruta actual de tu carpeta de trabajo
set "RUTA_ACTUAL=%~dp0"
set "RUTA_ACTUAL=%RUTA_ACTUAL:~0,-1%"

:: Nombre de la ruta virtual en tu navegador
set "NOMBRE_VIRTUAL=clinident_local"

:: Eliminar enlace previo si existía para evitar errores de Windows
if exist "C:\xampp\htdocs\%NOMBRE_VIRTUAL%" rmdir "C:\xampp\htdocs\%NOMBRE_VIRTUAL%"

:: Crear el acceso directo inteligente que leerá XAMPP
mklink /D "C:\xampp\htdocs\%NOMBRE_VIRTUAL%" "%RUTA_ACTUAL%"

echo.
echo =======================================================
echo     INICIANDO SERVIDORES DE XAMPP (APACHE + MYSQL)
echo =======================================================
echo.

:: Ir a la ubicación nativa de XAMPP e iniciar los servicios
cd /d C:\xampp
start "" xampp_start.exe

:: Pausa de 3 segundos para que Apache cargue correctamente
timeout /t 3 /nobreak >nul

echo.
echo =======================================================
echo     ABRIENDO REDIRECCIONADOR DE ENTRADA CLÍNIDENT
echo =======================================================
echo.

:: El navegador abrirá la raíz. Tu index.html ejecutará el "refresh" hacia ./login/login.html
start http://localhost/%NOMBRE_VIRTUAL%/

echo [OK] Entorno ejecutándose correctamente.
echo [INFO] Puedes minimizar esta consola de comandos.
echo.
pause