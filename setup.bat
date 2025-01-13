@echo off
setlocal

set VENV=.winvenv
set REQUIREMENTS=requirements.txt
set PYTHON=python

if "%1" == "install" goto install
if "%1" == "run" goto run
if "%1" == "get" goto get
if "%1" == "test" goto test
if "%1" == "clean" goto clean
goto end

:venv
if not exist %VENV% (
    %PYTHON% -m venv %VENV%
    call %VENV%\Scripts\pip install --upgrade pip
)
goto :eof

:install
call :venv
if exist %REQUIREMENTS% (
    call %VENV%\Scripts\pip install -r %REQUIREMENTS%
)
goto :eof

:run
call :install
call %VENV%\Scripts\python ss_uploader.py set
goto :eof

:get
call :install
call %VENV%\Scripts\python ss_uploader.py get
goto :eof

:test
call :install
call %VENV%\Scripts\python ss_uploader.py test
goto :eof

:clean
if exist %VENV% (
    rmdir /S /Q %VENV%
)
goto :eof

:end
echo Usage: %0 ^(install^|run^|get^|test^|clean^)
endlocal
