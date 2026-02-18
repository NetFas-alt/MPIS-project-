Этап 5. Архитектура уровня “слои и модули” (HLD)
Файл: docs/05_architecture_layers.md

Архитектурный стиль: Чистая архитектура / MVVM.

Слои:

UI (Presentation): View (окна, виджеты) + ViewModel (состояние экрана, команды).

Application (Use Cases): Сценарии использования (получить погоду для города, управлять избранным).

Domain: Бизнес-сущности (CurrentWeather, Location).

Infrastructure (Data): Репозитории (получение данных из API, чтение/запись файлов, кэш).

Модули + ответственность:

WeatherViewModule: Отвечает за отрисовку главного окна и обработку ввода пользователя.

WeatherViewModelModule: Хранит состояние (текущая погода, загрузка, ошибка) и команды для обновления.

WeatherUseCaseModule: Реализует сценарий "получить погоду": вызывает Geo-провайдер для поиска координат, затем Weather-провайдер для получения погоды по координатам.

GeoProviderModule: Инкапсулирует логику вызова API геокодинга и парсинг ответа.

WeatherProviderModule: Инкапсулирует логику вызова погодного API.

StorageModule: Отвечает за чтение/запись favorites.json и settings.json.

CacheModule: Хранит в памяти недавно полученные данные о погоде.

Правило зависимостей: Зависимости направлены внутрь. UI зависит от Application и Domain. Application зависит от Domain и абстракций Infrastructure. Infrastructure зависит от Domain. Нижние слои не знают о верхних.
