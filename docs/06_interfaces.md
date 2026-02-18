Этап 6. Детальный дизайн
Файл: docs/06_interfaces.md

IWeatherProvider: get_current(location) -> CurrentWeather, get_forecast(location, days) -> List[DailyForecast]

IGeoProvider: search(query: str) -> List[Location]

IStorage: load_favorites() -> List[str], save_favorites(List[str]), load_settings() -> Settings, save_settings(Settings)

ICache: get(key) -> Optional[CurrentWeather|List[DailyForecast]], set(key, value, ttl)

Типы ошибок (AppError): CityNotFoundError, NetworkError, RateLimitError, InvalidInputError, StorageError
