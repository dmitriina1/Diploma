@echo off
echo Останавливаем все контейнеры...
docker-compose down --remove-orphans
echo Готово!
pause
