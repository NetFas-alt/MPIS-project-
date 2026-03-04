#!/usr/bin/env python3
"""
WeatherEye - CLI приложение для просмотра погоды
Единый файл, содержит всё необходимое для работы.
"""

import os
import sys
import json
import argparse
import requests
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum


# ==================== КОНФИГУРАЦИЯ ====================

class Settings:
    """Настройки приложения"""
    # API ключи (для демо используем открытые API)
    GEO_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
    WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
    
    # Параметры приложения
    DEFAULT_UNITS = "C"
    DEFAULT_FORECAST_DAYS = 3
    CACHE_TTL_MINUTES = 10
    NETWORK_TIMEOUT_SECONDS = 5
    
    # Пути для хранения данных
    APP_DATA_DIR = Path.home() / ".weathereye"
    FAVORITES_FILE = APP_DATA_DIR / "favorites.json"
    SETTINGS_FILE = APP_DATA_DIR / "settings.json"
    
    @classmethod
    def ensure_dirs(cls):
        """Создание директорий для хранения данных"""
        cls.APP_DATA_DIR.mkdir(exist_ok=True)

# Инициализация директорий
Settings.ensure_dirs()


# ==================== DOMAIN МОДЕЛИ ====================

@dataclass
class Location:
    """Географическое местоположение"""
    name: str
    country: str
    latitude: float
    longitude: float
    
    def __str__(self):
        return f"{self.name}, {self.country}"


@dataclass
class CurrentWeather:
    """Текущая погода"""
    location: Location
    temperature: float      # в градусах Цельсия
    feels_like: float       # в градусах Цельсия
    humidity: int           # 0-100%
    wind_speed: float       # м/с
    description: str
    icon: str
    last_updated: datetime
    
    @property
    def temperature_c(self) -> float:
        return self.temperature
    
    @property
    def temperature_f(self) -> float:
        return (self.temperature * 9/5) + 32


@dataclass
class DailyForecast:
    """Прогноз на день"""
    location: Location
    date: datetime
    min_temperature: float
    max_temperature: float
    description: str
    icon: str


@dataclass
class AppSettings:
    """Настройки приложения"""
    units: str = "C"  # "C" или "F"
    
    def validate(self):
        if self.units not in ("C", "F"):
            raise ValueError("Units must be 'C' or 'F'")


# ==================== ОШИБКИ ====================

class ErrorType(Enum):
    """Типы ошибок приложения"""
    NOT_FOUND = "not_found"
    NETWORK = "network"
    RATE_LIMIT = "rate_limit"
    INVALID_INPUT = "invalid_input"
    STORAGE = "storage"
    UNKNOWN = "unknown"


class AppError(Exception):
    """Базовый класс для ошибок приложения"""
    def __init__(self, message: str, error_type: ErrorType, original_error: Exception = None):
        self.message = message
        self.error_type = error_type
        self.original_error = original_error
        super().__init__(self.message)


class CityNotFoundError(AppError):
    def __init__(self, city: str):
        super().__init__(
            f"City not found: '{city}'",
            ErrorType.NOT_FOUND
        )


class NetworkError(AppError):
    def __init__(self, original_error: Exception = None):
        super().__init__(
            "Network problem. Check your connection and try again later.",
            ErrorType.NETWORK,
            original_error
        )


class RateLimitError(AppError):
    def __init__(self):
        super().__init__(
            "Rate limit exceeded. Wait a few seconds and retry.",
            ErrorType.RATE_LIMIT
        )


class InvalidInputError(AppError):
    def __init__(self, message: str):
        super().__init__(
            message,
            ErrorType.INVALID_INPUT
        )


class StorageError(AppError):
    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(
            message,
            ErrorType.STORAGE,
            original_error
        )


# ==================== DTO ====================

@dataclass
class GeoApiResponseDTO:
    """DTO для ответа API геокодинга"""
    results: List[Dict[str, Any]] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GeoApiResponseDTO':
        return cls(results=data.get("results", []))


@dataclass
class WeatherApiResponseDTO:
    """DTO для ответа API погоды"""
    latitude: float
    longitude: float
    current: Dict[str, Any]
    daily: Dict[str, List]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WeatherApiResponseDTO':
        return cls(
            latitude=data.get("latitude", 0),
            longitude=data.get("longitude", 0),
            current=data.get("current", {}),
            daily=data.get("daily", {})
        )


@dataclass
class FavoritesFileDTO:
    """DTO для файла с избранными городами"""
    cities: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, List[str]]:
        return {"cities": self.cities}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FavoritesFileDTO':
        return cls(cities=data.get("cities", []))


@dataclass
class SettingsFileDTO:
    """DTO для файла настроек"""
    units: str = "C"
    
    def to_dict(self) -> Dict[str, str]:
        return {"units": self.units}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SettingsFileDTO':
        return cls(units=data.get("units", "C"))


# ==================== КЭШ ====================

class CacheEntry:
    """Запись в кэше"""
    def __init__(self, value: Any, ttl_minutes: int):
        self.value = value
        self.expires_at = datetime.now() + timedelta(minutes=ttl_minutes)
    
    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at


class Cache:
    """Простой in-memory кэш"""
    
    def __init__(self):
        self._storage: Dict[str, CacheEntry] = {}
        self.default_ttl = Settings.CACHE_TTL_MINUTES
    
    def get(self, key: str) -> Optional[Any]:
        """Получение значения из кэша"""
        entry = self._storage.get(key)
        if entry and not entry.is_expired:
            return entry.value
        elif entry and entry.is_expired:
            del self._storage[key]
        return None
    
    def set(self, key: str, value: Any, ttl_minutes: Optional[int] = None):
        """Сохранение значения в кэш"""
        ttl = ttl_minutes if ttl_minutes is not None else self.default_ttl
        self._storage[key] = CacheEntry(value, ttl)
    
    def clear(self):
        """Очистка кэша"""
        self._storage.clear()
    
    def remove(self, key: str):
        """Удаление конкретного ключа"""
        if key in self._storage:
            del self._storage[key]


# ==================== ПРОВАЙДЕРЫ ====================

class GeoProvider:
    """Провайдер для геокодинга (поиск координат по названию города)"""
    
    def __init__(self):
        self.base_url = Settings.GEO_API_URL
        self.timeout = Settings.NETWORK_TIMEOUT_SECONDS
    
    def search(self, query: str) -> List[Location]:
        """
        Поиск города по названию
        Возвращает список возможных местоположений
        """
        if not query or not query.strip():
            return []
        
        try:
            params = {
                "name": query.strip(),
                "count": 5,
                "language": "ru",
                "format": "json"
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            dto = GeoApiResponseDTO.from_dict(data)
            
            locations = []
            for result in dto.results:
                locations.append(Location(
                    name=result.get("name", ""),
                    country=result.get("country", ""),
                    latitude=result.get("latitude", 0),
                    longitude=result.get("longitude", 0)
                ))
            
            if not locations:
                raise CityNotFoundError(query)
            
            return locations
            
        except requests.exceptions.Timeout:
            raise NetworkError()
        except requests.exceptions.ConnectionError:
            raise NetworkError()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise RateLimitError()
            raise NetworkError()
        except Exception as e:
            raise NetworkError(e)


class WeatherProvider:
    """Провайдер для получения данных о погоде"""
    
    def __init__(self):
        self.base_url = Settings.WEATHER_API_URL
        self.timeout = Settings.NETWORK_TIMEOUT_SECONDS
    
    def get_current(self, location: Location) -> CurrentWeather:
        """Получение текущей погоды для местоположения"""
        try:
            params = {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
                "timezone": "auto"
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            dto = WeatherApiResponseDTO.from_dict(data)
            
            # Преобразование кода погоды в описание
            weather_code = dto.current.get("weather_code", 0)
            description = self._code_to_description(weather_code)
            
            return CurrentWeather(
                location=location,
                temperature=dto.current.get("temperature_2m", 0),
                feels_like=dto.current.get("apparent_temperature", 0),
                humidity=dto.current.get("relative_humidity_2m", 0),
                wind_speed=dto.current.get("wind_speed_10m", 0) / 3.6,  # км/ч -> м/с
                description=description,
                icon=self._code_to_icon(weather_code),
                last_updated=datetime.now()
            )
            
        except requests.exceptions.Timeout:
            raise NetworkError()
        except requests.exceptions.ConnectionError:
            raise NetworkError()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise RateLimitError()
            raise NetworkError()
        except Exception as e:
            raise NetworkError(e)
    
    def get_forecast(self, location: Location, days: int = 3) -> List[DailyForecast]:
        """Получение прогноза на N дней"""
        if days < 1 or days > 7:
            days = 3
            
        try:
            params = {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "daily": "weather_code,temperature_2m_max,temperature_2m_min",
                "forecast_days": days,
                "timezone": "auto"
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            dto = WeatherApiResponseDTO.from_dict(data)
            
            forecasts = []
            daily = dto.daily
            
            dates = daily.get("time", [])
            max_temps = daily.get("temperature_2m_max", [])
            min_temps = daily.get("temperature_2m_min", [])
            weather_codes = daily.get("weather_code", [])
            
            for i in range(min(len(dates), days)):
                date = datetime.fromisoformat(dates[i])
                weather_code = weather_codes[i] if i < len(weather_codes) else 0
                
                forecasts.append(DailyForecast(
                    location=location,
                    date=date,
                    min_temperature=min_temps[i] if i < len(min_temps) else 0,
                    max_temperature=max_temps[i] if i < len(max_temps) else 0,
                    description=self._code_to_description(weather_code),
                    icon=self._code_to_icon(weather_code)
                ))
            
            return forecasts
            
        except requests.exceptions.Timeout:
            raise NetworkError()
        except requests.exceptions.ConnectionError:
            raise NetworkError()
        except Exception as e:
            raise NetworkError(e)
    
    def _code_to_description(self, code: int) -> str:
        """Преобразование WMO кода в текстовое описание"""
        descriptions = {
            0: "Ясно",
            1: "Преимущественно ясно",
            2: "Переменная облачность",
            3: "Пасмурно",
            45: "Туман",
            48: "Изморозь",
            51: "Легкая морось",
            53: "Морось",
            55: "Сильная морось",
            61: "Небольшой дождь",
            63: "Дождь",
            65: "Сильный дождь",
            71: "Небольшой снег",
            73: "Снег",
            75: "Сильный снег",
            80: "Ливень",
            81: "Сильный ливень",
            95: "Гроза",
        }
        return descriptions.get(code, "Неизвестно")
    
    def _code_to_icon(self, code: int) -> str:
        """Преобразование WMO кода в иконку"""
        if code == 0:
            return "☀️"
        elif code in (1, 2):
            return "⛅"
        elif code == 3:
            return "☁️"
        elif code in (45, 48):
            return "🌫️"
        elif code in (51, 53, 55, 61, 63, 65, 80, 81):
            return "🌧️"
        elif code in (71, 73, 75):
            return "❄️"
        elif code == 95:
            return "⛈️"
        else:
            return "🌡️"


# ==================== ХРАНИЛИЩЕ ====================

class Storage:
    """Хранилище для настроек и избранных городов"""
    
    def __init__(self):
        self.favorites_file = Settings.FAVORITES_FILE
        self.settings_file = Settings.SETTINGS_FILE
    
    def load_favorites(self) -> List[str]:
        """Загрузка списка избранных городов"""
        try:
            if not self.favorites_file.exists():
                return []
            
            with open(self.favorites_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                dto = FavoritesFileDTO.from_dict(data)
                return dto.cities
                
        except json.JSONDecodeError as e:
            raise StorageError("Failed to parse favorites file", e)
        except Exception as e:
            raise StorageError("Failed to load favorites", e)
    
    def save_favorites(self, cities: List[str]):
        """Сохранение списка избранных городов"""
        try:
            dto = FavoritesFileDTO(cities=cities)
            with open(self.favorites_file, 'w', encoding='utf-8') as f:
                json.dump(dto.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise StorageError("Failed to save favorites", e)
    
    def load_settings(self) -> AppSettings:
        """Загрузка настроек"""
        try:
            if not self.settings_file.exists():
                return AppSettings()
            
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                dto = SettingsFileDTO.from_dict(data)
                settings = AppSettings(units=dto.units)
                settings.validate()
                return settings
                
        except json.JSONDecodeError as e:
            raise StorageError("Failed to parse settings file", e)
        except Exception as e:
            raise StorageError("Failed to load settings", e)
    
    def save_settings(self, settings: AppSettings):
        """Сохранение настроек"""
        try:
            settings.validate()
            dto = SettingsFileDTO(units=settings.units)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(dto.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise StorageError("Failed to save settings", e)


# ==================== СЦЕНАРИИ ИСПОЛЬЗОВАНИЯ ====================

class WeatherUseCase:
    """Сценарий: получение погоды для города"""
    
    def __init__(self):
        self.geo_provider = GeoProvider()
        self.weather_provider = WeatherProvider()
        self.cache = Cache()
    
    def execute(self, city: str, units: str = "C") -> Tuple[CurrentWeather, List[DailyForecast]]:
        """
        Выполнение сценария: поиск города и получение погоды
        Возвращает (текущая_погода, прогноз)
        """
        if not city or not city.strip():
            raise InvalidInputError("City is required")
        
        # Проверка кэша
        cache_key = f"{city.strip().lower()}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        # Поиск города
        locations = self.geo_provider.search(city)
        if not locations:
            raise CityNotFoundError(city)
        
        # Берем первый результат
        location = locations[0]
        
        # Получаем погоду
        current = self.weather_provider.get_current(location)
        forecast = self.weather_provider.get_forecast(location, 3)
        
        result = (current, forecast)
        
        # Сохраняем в кэш
        self.cache.set(cache_key, result)
        
        return result


class FavoritesUseCase:
    """Сценарий: управление избранными городами"""
    
    def __init__(self):
        self.storage = Storage()
    
    def list_favorites(self) -> List[str]:
        """Получить список избранных городов"""
        return self.storage.load_favorites()
    
    def add_favorite(self, city: str) -> List[str]:
        """Добавить город в избранное"""
        if not city or not city.strip():
            raise InvalidInputError("City name cannot be empty")
        
        favorites = self.storage.load_favorites()
        city_clean = city.strip()
        
        if city_clean not in favorites:
            favorites.append(city_clean)
            self.storage.save_favorites(favorites)
        
        return favorites
    
    def remove_favorite(self, city: str) -> List[str]:
        """Удалить город из избранного"""
        if not city or not city.strip():
            raise InvalidInputError("City name cannot be empty")
        
        favorites = self.storage.load_favorites()
        city_clean = city.strip()
        
        if city_clean in favorites:
            favorites.remove(city_clean)
            self.storage.save_favorites(favorites)
        
        return favorites


class SettingsUseCase:
    """Сценарий: управление настройками"""
    
    def __init__(self):
        self.storage = Storage()
    
    def get_settings(self) -> AppSettings:
        """Получить текущие настройки"""
        return self.storage.load_settings()
    
    def set_units(self, units: str) -> AppSettings:
        """Установить единицы измерения"""
        if units.upper() not in ("C", "F"):
            raise InvalidInputError("Units must be 'C' or 'F'")
        
        settings = self.storage.load_settings()
        settings.units = units.upper()
        self.storage.save_settings(settings)
        return settings


# ==================== ФОРМАТТЕРЫ ====================

def format_temperature(temp_c: float, units: str) -> str:
    """Форматирование температуры в зависимости от единиц"""
    if units.upper() == "F":
        temp = (temp_c * 9/5) + 32
        return f"{temp:.0f}°F"
    return f"{temp_c:.0f}°C"


def format_wind(speed_ms: float) -> str:
    """Форматирование скорости ветра"""
    return f"{speed_ms:.1f} м/с"


def format_current_weather(weather: CurrentWeather, units: str) -> str:
    """Форматирование текущей погоды для вывода"""
    temp = format_temperature(weather.temperature, units)
    feels = format_temperature(weather.feels_like, units)
    
    return (
        f"{weather.location.name}, {weather.location.country} "
        f"(обновлено: {weather.last_updated.strftime('%H:%M')})\n"
        f"{weather.icon} Температура: {temp} (ощущается как {feels})\n"
        f"💧 Влажность: {weather.humidity}%\n"
        f"💨 Ветер: {format_wind(weather.wind_speed)}\n"
        f"☁️ Описание: {weather.description}"
    )


def format_forecast(forecasts: List[DailyForecast], units: str) -> str:
    """Форматирование прогноза для вывода"""
    if not forecasts:
        return "Нет данных прогноза"
    
    result = ["Прогноз на ближайшие дни:", 
              "Дата       | Мин/Макс | Описание",
              "-" * 40]
    
    for forecast in forecasts:
        date = forecast.date.strftime("%Y-%m-%d")
        min_temp = format_temperature(forecast.min_temperature, units)
        max_temp = format_temperature(forecast.max_temperature, units)
        temp_range = f"{min_temp}/{max_temp}"
        
        result.append(f"{date} | {temp_range:<10} | {forecast.description}")
    
    return "\n".join(result)


# ==================== ГЛАВНОЕ CLI ПРИЛОЖЕНИЕ ====================

class WeatherApp:
    """Главный класс CLI приложения"""
    
    def __init__(self):
        self.weather_use_case = WeatherUseCase()
        self.favorites_use_case = FavoritesUseCase()
        self.settings_use_case = SettingsUseCase()
        self.settings = self.settings_use_case.get_settings()
    
    def run(self):
        """Запуск приложения с парсингом аргументов"""
        parser = self._create_parser()
        args = parser.parse_args()
        
        if not hasattr(args, 'func'):
            parser.print_help()
            return
        
        try:
            args.func(args)
        except AppError as e:
            self._handle_error(e)
        except KeyboardInterrupt:
            print("\n👋 До свидания!")
        except Exception as e:
            print(f"❌ Неизвестная ошибка: {e}")
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Создание парсера аргументов командной строки"""
        parser = argparse.ArgumentParser(
            description="WeatherEye - узнай погоду в любом городе",
            epilog="Пример: weather now Moscow"
        )
        subparsers = parser.add_subparsers(title="команды", dest="command")
        
        # Команда: now
        now_parser = subparsers.add_parser("now", help="текущая погода")
        now_parser.add_argument("city", help="название города")
        now_parser.set_defaults(func=self._cmd_now)
        
        # Команда: forecast
        forecast_parser = subparsers.add_parser("forecast", help="прогноз погоды")
        forecast_parser.add_argument("city", help="название города")
        forecast_parser.add_argument("--days", type=int, default=3, help="количество дней (1-5)")
        forecast_parser.set_defaults(func=self._cmd_forecast)
        
        # Команды для избранного
        fav_parser = subparsers.add_parser("favorites", help="управление избранным")
        fav_subparsers = fav_parser.add_subparsers(dest="fav_command")
        
        fav_list = fav_subparsers.add_parser("list", help="показать избранные города")
        fav_list.set_defaults(func=self._cmd_fav_list)
        
        fav_add = fav_subparsers.add_parser("add", help="добавить город в избранное")
        fav_add.add_argument("city", help="название города")
        fav_add.set_defaults(func=self._cmd_fav_add)
        
        fav_remove = fav_subparsers.add_parser("remove", help="удалить город из избранного")
        fav_remove.add_argument("city", help="название города")
        fav_remove.set_defaults(func=self._cmd_fav_remove)
        
        # Команды для настроек
        settings_parser = subparsers.add_parser("settings", help="настройки")
        settings_subparsers = settings_parser.add_subparsers(dest="settings_command")
        
        settings_show = settings_subparsers.add_parser("show", help="показать настройки")
        settings_show.set_defaults(func=self._cmd_settings_show)
        
        settings_units = settings_subparsers.add_parser("units", help="установить единицы измерения")
        settings_units.add_argument("value", choices=["C", "F"], help="C или F")
        settings_units.set_defaults(func=self._cmd_settings_units)
        
        return parser
    
    def _cmd_now(self, args):
        """Обработка команды now"""
        print(f"🔍 Загрузка погоды для {args.city}...")
        
        current, _ = self.weather_use_case.execute(args.city, self.settings.units)
        
        print()
        print(format_current_weather(current, self.settings.units))
    
    def _cmd_forecast(self, args):
        """Обработка команды forecast"""
        if args.days < 1 or args.days > 5:
            print("❌ Количество дней должно быть от 1 до 5")
            return
        
        print(f"🔍 Загрузка прогноза для {args.city} на {args.days} дней...")
        
        _, forecast = self.weather_use_case.execute(args.city, self.settings.units)
        
        print()
        print(format_forecast(forecast[:args.days], self.settings.units))
    
    def _cmd_fav_list(self, args):
        """Показать список избранных городов"""
        favorites = self.favorites_use_case.list_favorites()
        
        if not favorites:
            print("📭 Список избранных городов пуст")
            return
        
        print("📋 Список избранных городов:")
        for i, city in enumerate(favorites, 1):
            print(f"  {i}. {city}")
    
    def _cmd_fav_add(self, args):
        """Добавить город в избранное"""
        favorites = self.favorites_use_case.add_favorite(args.city)
        print(f"✅ Город '{args.city}' добавлен в избранное")
    
    def _cmd_fav_remove(self, args):
        """Удалить город из избранного"""
        favorites = self.favorites_use_case.remove_favorite(args.city)
        print(f"🗑️ Город '{args.city}' удален из избранного")
    
    def _cmd_settings_show(self, args):
        """Показать текущие настройки"""
        settings = self.settings_use_case.get_settings()
        units_display = "Цельсий (°C)" if settings.units == "C" else "Фаренгейт (°F)"
        
        print("⚙️ Текущие настройки:")
        print(f"  • Единицы измерения: {units_display}")
        print(f"  • Директория данных: {self.settings_use_case.storage.favorites_file.parent}")
    
    def _cmd_settings_units(self, args):
        """Установить единицы измерения"""
        self.settings = self.settings_use_case.set_units(args.value)
        units_display = "Цельсий (°C)" if args.value == "C" else "Фаренгейт (°F)"
        print(f"✅ Единицы измерения изменены на {units_display}")
    
    def _handle_error(self, error: AppError):
        """Обработка ошибок приложения"""
        messages = {
            ErrorType.NOT_FOUND: "🔍",
            ErrorType.NETWORK: "🌐",
            ErrorType.RATE_LIMIT: "⏳",
            ErrorType.INVALID_INPUT: "❌",
            ErrorType.STORAGE: "💾",
            ErrorType.UNKNOWN: "⚠️"
        }
        
        emoji = messages.get(error.error_type, "❌")
        print(f"{emoji} Error: {error.message}")


# ==================== ТОЧКА ВХОДА ====================

def main():
    """Точка входа в приложение"""
    app = WeatherApp()
    app.run()


if __name__ == "__main__":
    main()
