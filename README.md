# RoutingApp

## Приложение для построения оптимальных маршрутов по городу

### О проекте

RoutingApp — это настольное приложение на Python для построения оптимального маршрута между двумя и более точками с учётом типа передвижения (пешком или на автомобиле) и выбранного критерия оптимизации (по времени или расстоянию). Программа позволяет визуализировать маршрут на карте и сохранять результаты в базу данных SQL Server для последующего анализа.

### Возможности

* Построение маршрутов с промежуточными точками.
* Выбор типа передвижения (пешком, на машине).
* Оптимизация маршрута по расстоянию или времени.
* Визуализация маршрута на интерактивной HTML-карте.
* Сохранение маршрутов в базу данных.
* Просмотр истории построенных маршрутов.

### Установка

1. Убедитесь, что у вас установлен Python 3.10+ и пакетный менеджер [uv](https://github.com/astral-sh/uv).
2. Список всех требуемых библиотек для работы программы находятся в файле requirements.txt.Установите зависимости:

```bash
pip install uv
uv init
uv add -r requirements.txt
```

### Запуск приложения

```bash
uv run route_app.py
```

### Структура проекта

```
app/
  ├── configs/
  │     └── settings.py         # Конфигурационные параметры приложения
  ├── routing/
  │     └── map_utils.py        # Логика маршрутизации и построения графа
data/                           # Директория для хранения кэшированных карт городов
tests/
  ├── test_database.py          # Тесты базы данных
  ├── test_routing.py           # Тесты алгоритмов маршрутизации
  ├── test_gui.py               # Тесты графического интерфейса
  └── test_main.py              # Общий запуск всех тестов
map_route.html                  # Шаблон карты маршрута
route_app.py                    # Главный запуск приложения
requirements.txt                # Зависимости проекта
```

### Расширение карты для другого города

Чтобы построить маршрут в другом городе:

1. Укажите название города в настройках интерфейса.
2. Программа автоматически загрузит и сохранит граф дорожной сети для выбранного города.

### Авторы
Качалова Анастасия Алексеевна.
Разработано в рамках ВКР 2025.
