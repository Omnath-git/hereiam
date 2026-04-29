@echo off
set "KEY=D:\Hereiam.in V5\Update Server\private ssh-key-2026-04-27.key"

:: Fix permissions silently
icacls "%KEY%" /inheritance:r >nul 2>&1
icacls "%KEY%" /grant:r "%username%":"(R)" >nul 2>&1

echo Deploying Updates to Hereiam Server...

:: पूरी कमांड को एक ही लाइन में बिना किसी स्पेस या एंटर के (One-Line Execution)
ssh -i "%KEY%" ubuntu@161.118.191.181 "bash -c 'cd /home/ubuntu/hereiam_portal && source ../venv/bin/activate && cd /home/ubuntu/hereiam_portal/hereiam && git fetch --all && git reset --hard origin/master && sudo pkill gunicorn || true && /home/ubuntu/hereiam_portal/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 \"app:create_app()\" --daemon && sudo systemctl restart nginx'"

echo.
echo -------------------------------------------
echo   SERVER UPDATED SUCCESSFULLY!
echo -------------------------------------------
pause