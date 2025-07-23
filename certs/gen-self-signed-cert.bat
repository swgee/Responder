@echo off
REM Generate self-signed SSL certificate for Responder on Windows

set CERT_DIR=%~dp0
set KEY_FILE=%CERT_DIR%responder.key
set CRT_FILE=%CERT_DIR%responder.crt

echo Generating self-signed SSL certificate for Responder...

REM Try OpenSSL first
where openssl >nul 2>&1
if %errorLevel% equ 0 (
    echo Using OpenSSL to generate certificate...
    openssl req -new -x509 -keyout "%KEY_FILE%" -out "%CRT_FILE%" -days 365 -nodes -subj "/C=US/ST=Local/L=Local/O=Responder/CN=responder"
    if %errorLevel% equ 0 (
        echo Certificate generated successfully using OpenSSL
        goto :end
    )
)

REM Fallback to PowerShell
echo OpenSSL not found, using PowerShell to generate certificate...
powershell -Command "& {$cert = New-SelfSignedCertificate -Subject 'CN=responder' -CertStoreLocation 'Cert:\CurrentUser\My' -KeyExportPolicy Exportable -KeySpec Signature -KeyLength 2048 -KeyAlgorithm RSA -HashAlgorithm SHA256; Export-Certificate -Cert $cert -FilePath '%CRT_FILE%'; $pwd = ConvertTo-SecureString -String 'responder' -Force -AsPlainText; Export-PfxCertificate -Cert $cert -FilePath '%CERT_DIR%responder.pfx' -Password $pwd}"

if %errorLevel% equ 0 (
    echo Certificate generated successfully using PowerShell
) else (
    echo Failed to generate certificate. Please install OpenSSL or ensure PowerShell is available.
)

:end 