Файл: docs/06_class_diagram.md (описание текстом)

MainWindow (View) -> зависит от MainViewModel.

MainViewModel (наследует Observable) содержит CurrentWeather, List<DailyForecast>, is_loading и ссылку на WeatherUseCase.

WeatherUseCase зависит от IGeoProvider, IWeatherProvider, ICache.

YandexGeoProvider (реализует IGeoProvider) зависит от HTTP-клиента.

OpenWeatherMapProvider (реализует IWeatherProvider) зависит от HTTP-клиента.

JsonFileStorage (реализует IStorage) работает с файловой системой.

InMemoryCache (реализует ICache) хранит dict.
