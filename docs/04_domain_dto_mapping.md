Этап 4. Модель предметной области + DTO + маппинг
Файл: docs/04_domain_dto_mapping.md

Domain-модели:

Location (city_name, country_code)

CurrentWeather (location, temperature_c, feels_like_c, humidity_percent, wind_speed_ms, description, icon_code, last_updated)

DailyForecast (location, date, min_temp_c, max_temp_c, description, icon_code)

AppSettings (units: 'C' | 'F')

FavoriteLocation (name, country_code)

DTO (внешние данные):

GeoApiResponseDTO (список мест от сервиса геокодинга)

WeatherApiResponseDTO (сырой ответ от погодного API)

FavoritesFileDTO (список строк с названиями городов)

SettingsFileDTO (объект с полем units)

Инварианты и ограничения данных:

Влажность: 0 <= humidity <= 100.

Температура в градусах Цельсия: теоретически может быть ниже абсолютного нуля, но API должен возвращать корректные значения. Приложение не ограничивает.

Количество дней прогноза: 1 <= days <= 5.

Название города не может быть пустой строкой.

Таблица “DTO -> Domain”:

DTO Поле	                              Domain Поле	                  Преобразование/Правило
WeatherApiResponseDTO.temp_c	          CurrentWeather.temperature_c	Прямое присвоение.
WeatherApiResponseDTO.condition.text	  CurrentWeather.description	  Прямое присвоение.
WeatherApiResponseDTO.wind_kph	        CurrentWeather.wind_speed_ms	wind_kph / 3.6 (округление до 1 знака)
FavoritesFileDTO[]	                    List<FavoriteLocation>	      Для каждой строки создается FavoriteLocation(name=string)
SettingsFileDTO.units	                  AppSettings.units	            Если значение не 'F', по умолчанию 'C'.
