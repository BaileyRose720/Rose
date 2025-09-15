@echo off
setlocal
cd /d C:\RoseAI
REM Use venv python if present; fall back to system python
IF EXIST C:\RoseAi\.venv\Scripts\python.exe (
    set PY=C:\Rose\.venv\Scripts\python.exe
) EKSE (
    set PY=python.exe
)

REM Log all output (including errors) so we can debut if it dies
if not exist  C:\RoseAI\runtime\logs mkdir C:\RoseAI\runtime\logs
"%PY%" "C:\RoseAI\core\rose_service.py" >> C:\RoseAi\runtime\logs\rose_service.log 2>&1