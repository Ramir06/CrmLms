@echo off
cd /d "c:\Users\Admin\Desktop\CRM LMS — копия"
call .venv\Scripts\activate
cd crm_lms
python manage.py runserver
pause
