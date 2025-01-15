@echo off
setlocal

set VENV=.winvenv
set REQUIREMENTS=requirements.txt
set PYTHON=python

if not exist %VENV% (
    %PYTHON% -m venv %VENV%
    call %VENV%\Scripts\pip install --upgrade pip
)

:install
if exist %REQUIREMENTS% (
    call %VENV%\Scripts\pip install -r %REQUIREMENTS%
) else (
    echo Requirements file not found!
    exit /b 1
)

:run
call :install
call %VENV%\Scripts\python create_config.py
call %VENV%\Scripts\python ss_uploader.py set
exit /b

:get
call :install
call %VENV%\Scripts\python ss_uploader.py get
exit /b

:test
call :install
call %VENV%\Scripts\python ss_uploader.py test
exit /b

:clean
if exist %VENV% (
    rmdir /s /q %VENV%
)
exit /b
