@echo off
REM Responder Windows Launcher
REM Usage: Windows_launcher.bat interface responder_options

echo Starting Responder for Windows...

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo ERROR: This script must be run as Administrator
    echo Right-click and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

REM Stop conflicting Windows services
echo Stopping potentially conflicting Windows services...

REM Stop Windows Defender Network Protection if running
sc query WinDefend >nul 2>&1
if %errorLevel% equ 0 (
    echo Temporarily stopping Windows Defender Service...
    net stop WinDefend >nul 2>&1
)

REM Stop DNS Client service temporarily
echo Stopping DNS Client service...
net stop Dnscache >nul 2>&1

REM Stop Windows DHCP Client
echo Stopping DHCP Client service...
net stop Dhcp >nul 2>&1

REM Get the interface name from first parameter
set INTERFACE=%1
set RESPONDER_PATH=%~dp0
set RESPONDER_OPTIONS=%2 %3 %4 %5 %6 %7 %8 %9

REM Get IP address for the interface using PowerShell
for /f "tokens=*" %%i in ('powershell -Command "Get-NetIPAddress -InterfaceAlias '%INTERFACE%' -AddressFamily IPv4 | Select-Object -ExpandProperty IPAddress"') do set IP_ADDR=%%i

echo Using Interface: %INTERFACE%
echo Using IP Address: %IP_ADDR%

REM Launch Responder with the IP address
echo Launching Responder...
python "%RESPONDER_PATH%Responder.py" -i %IP_ADDR% %RESPONDER_OPTIONS%

REM Restore services after Responder exits
echo.
echo Restoring Windows services...

REM Restart DNS Client
echo Starting DNS Client service...
net start Dnscache >nul 2>&1

REM Restart DHCP Client
echo Starting DHCP Client service...
net start Dhcp >nul 2>&1

REM Restart Windows Defender if it was running
echo Starting Windows Defender service...
net start WinDefend >nul 2>&1

echo.
echo Responder session ended. Services restored.
pause 