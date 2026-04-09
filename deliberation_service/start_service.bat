@echo off
cd c:\Users\Dell\OneDrive\Bureau\microservices_uadb\deliberation_service
call venv\Scripts\activate.bat
cd deliberation_service
python manage.py migrate
python manage.py runserver 8004
pause
