Файл: docs/06_sequence_diagrams.md (описание текстом)

Сценарий "Поиск города и получение погоды":

Пользователь вводит "London" и нажимает Enter.

View вызывает ViewModel.search_city("London").

ViewModel устанавливает is_loading = true.

ViewModel вызывает WeatherUseCase.execute("London").

UseCase вызывает GeoProvider.search("London") -> получает координаты.

UseCase вызывает WeatherProvider.get_current(coords) и get_forecast(coords, 3).

UseCase возвращает данные в ViewModel.

ViewModel обновляет current_weather, forecast и устанавливает is_loading = false.

View автоматически обновляется.

Сценарий "Загрузка из избранного":

Пользователь кликает на "Paris" в списке избранного.

View вызывает ViewModel.load_favorite("Paris").

ViewModel проверяет наличие в ICache по ключу "Paris". Если есть -> использует кэш. Если нет -> вызывает WeatherUseCase (как в сценарии 1).

После получения данных (из кэша или сети) обновляет состояние, снимает флаг загрузки.
