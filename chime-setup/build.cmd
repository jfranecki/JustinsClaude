@echo off
rem Rebuilds chime.exe from chime.cs with the C# compiler that ships with Windows. Run it after editing chime.cs.
"%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe" /nologo /target:winexe /optimize+ /out:"%~dp0chime.exe" /r:System.Web.Extensions.dll "%~dp0chime.cs"
if errorlevel 1 (echo BUILD FAILED) else (echo built %~dp0chime.exe)
