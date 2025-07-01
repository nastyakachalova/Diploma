# settings.py

GRAPHML_FILENAME_DRIVE = "city_drive.graphml"
GRAPHML_FILENAME_WALK = "city_walk.graphml"

DB_CONFIG = {
    "server": "localhost",
    "database": "route_history",
    "trusted_connection": True,
    "driver": "ODBC Driver 17 for SQL Server"
}

CITIES = {
    "Краснодар": "Краснодар, Россия",
    "Москва": "Москва, Россия",
    "Санкт-Петербург": "Санкт-Петербург, Россия",
    "Сочи": "Сочи, Россия",
    "Ростов-на-Дону": "Ростов-на-Дону, Россия"
}