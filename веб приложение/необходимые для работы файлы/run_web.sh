#!/bin/bash
echo "Установка зависимостей..."
pip install -r requirements-web.txt
echo "Запуск веб-интерфейса WeatherEye..."
python web_app.py