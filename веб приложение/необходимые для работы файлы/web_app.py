#!/usr/bin/env python3
"""
WeatherEye Web Interface
Веб-оболочка для консольного приложения погоды
"""

import os
import sys
import json
import subprocess
import threading
from pathlib import Path
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import secrets

# Добавляем путь к вашему CLI приложению
CLI_PATH = Path(__file__).parent / "weather.py"

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
CORS(app)

# Конфигурация
app.config['JSON_AS_ASCII'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True


def run_cli_command(args):
    """Запуск CLI команды и получение результата"""
    try:
        # Формируем команду
        cmd = ['python', str(CLI_PATH)] + args
        
        # Запускаем процесс
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=30,
            env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
        )
        
        # Объединяем stdout и stderr для полного вывода
        output = result.stdout + result.stderr
        
        return {
            'success': result.returncode == 0,
            'output': output,
            'command': ' '.join(cmd)
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'output': '⚠️ Превышено время ожидания (30 секунд)'
        }
    except Exception as e:
        return {
            'success': False,
            'output': f'❌ Ошибка: {str(e)}'
        }


def get_favorites():
    """Получение списка избранных городов"""
    result = run_cli_command(['favorites', 'list'])
    if result['success']:
        # Парсим вывод для извлечения городов
        lines = result['output'].split('\n')
        favorites = []
        for line in lines:
            if "'" in line and line.strip().startswith(tuple('123456789')):
                # Извлекаем город между кавычками
                start = line.find("'")
                end = line.rfind("'")
                if start != -1 and end != -1 and start < end:
                    city = line[start+1:end]
                    favorites.append(city)
        return favorites
    return []


@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')


@app.route('/api/weather/now', methods=['POST'])
def weather_now():
    """API для текущей погоды"""
    data = request.json
    city = data.get('city', '').strip()
    units = data.get('units', 'C')
    
    if not city:
        return jsonify({'success': False, 'output': '❌ Введите название города'})
    
    # Устанавливаем единицы измерения
    if units != 'C':
        run_cli_command(['settings', 'units', units])
    
    # Получаем погоду
    result = run_cli_command(['now', city])
    return jsonify(result)


@app.route('/api/weather/forecast', methods=['POST'])
def weather_forecast():
    """API для прогноза"""
    data = request.json
    city = data.get('city', '').strip()
    days = data.get('days', 3)
    units = data.get('units', 'C')
    
    if not city:
        return jsonify({'success': False, 'output': '❌ Введите название города'})
    
    # Проверяем дни
    try:
        days = int(days)
        if days < 1 or days > 16:
            days = 3
    except:
        days = 3
    
    # Устанавливаем единицы измерения
    if units != 'C':
        run_cli_command(['settings', 'units', units])
    
    # Получаем прогноз
    result = run_cli_command(['forecast', city, '--days', str(days)])
    return jsonify(result)


@app.route('/api/favorites/list', methods=['GET'])
def favorites_list():
    """API для списка избранного"""
    result = run_cli_command(['favorites', 'list'])
    favorites = get_favorites()
    return jsonify({
        'success': result['success'],
        'favorites': favorites,
        'output': result['output']
    })


@app.route('/api/favorites/add', methods=['POST'])
def favorites_add():
    """API для добавления в избранное"""
    data = request.json
    city = data.get('city', '').strip()
    
    if not city:
        return jsonify({'success': False, 'output': '❌ Введите название города'})
    
    result = run_cli_command(['favorites', 'add', city])
    favorites = get_favorites()
    return jsonify({
        'success': result['success'],
        'favorites': favorites,
        'output': result['output']
    })


@app.route('/api/favorites/remove', methods=['POST'])
def favorites_remove():
    """API для удаления из избранного"""
    data = request.json
    city = data.get('city', '').strip()
    
    if not city:
        return jsonify({'success': False, 'output': '❌ Введите название города'})
    
    result = run_cli_command(['favorites', 'remove', city])
    favorites = get_favorites()
    return jsonify({
        'success': result['success'],
        'favorites': favorites,
        'output': result['output']
    })


@app.route('/api/settings/show', methods=['GET'])
def settings_show():
    """API для показа настроек"""
    result = run_cli_command(['settings', 'show'])
    return jsonify(result)


@app.route('/api/settings/units', methods=['POST'])
def settings_units():
    """API для смены единиц измерения"""
    data = request.json
    units = data.get('units', 'C')
    
    if units not in ['C', 'F']:
        return jsonify({'success': False, 'output': '❌ Единицы должны быть C или F'})
    
    result = run_cli_command(['settings', 'units', units])
    return jsonify(result)


if __name__ == '__main__':
    print("🌤️  WeatherEye Web Interface")
    print("=" * 40)
    print("🚀 Запуск сервера...")
    print("📁 CLI приложение:", CLI_PATH)
    print("🌐 Откройте в браузере: http://localhost:5000")
    print("=" * 40)
    app.run(debug=True, host='0.0.0.0', port=5000)