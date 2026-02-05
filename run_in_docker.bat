@echo off
echo [*] Starting Auto_VAPT in Docker Mode...
echo [*] This allows access to Nuclei and other tools installed in the container.

docker compose up --build
pause
