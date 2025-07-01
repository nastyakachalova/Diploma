# db_utils.py

import pyodbc
from loguru import logger
from app.configs.settings import DB_CONFIG

DB_NAME = DB_CONFIG["database"]

TABLES = {
    "Routes": (
        """
        IF OBJECT_ID('Routes', 'U') IS NULL
        CREATE TABLE Routes (
            id INT IDENTITY(1,1) PRIMARY KEY,
            start_address VARCHAR(255),
            end_address VARCHAR(255),
            transport_mode VARCHAR(50),
            optimization_mode VARCHAR(50),
            distance_km FLOAT,
            time_min FLOAT,
            timestamp DATETIME DEFAULT GETDATE()
        )
        """
    )
}

# Строка подключения к SQL Server
def get_connection(database=None):
    conn_str = (
        f"DRIVER={{{DB_CONFIG['driver']}}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={database if database else 'master'};"
    )
    
    if DB_CONFIG.get("trusted_connection", False):
        conn_str += "Trusted_Connection=yes;"
    else:
        # Если бы в настройках были логин и пароль
        conn_str += f"UID={DB_CONFIG.get('username', '')};"
        conn_str += f"PWD={DB_CONFIG.get('password', '')};"
        
    return pyodbc.connect(conn_str)

# Создание БД и таблиц
def initialize_database():
    try:
        # Подключение к master и проверка/создание базы
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(f"""
            IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = '{DB_NAME}')
            BEGIN
                CREATE DATABASE {DB_NAME}
            END
        """)
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"База данных '{DB_NAME}' проверена/создана.")


        # Подключение уже к нужной базе
        conn = get_connection(DB_NAME)
        cursor = conn.cursor()

        for table_name, ddl in TABLES.items():
            cursor.execute(ddl)
            logger.info(f"Таблица '{table_name}' проверена или создана.")

        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")

# Сохранение маршрута
def save_route_to_db(start, end, transport_mode, optimize_mode, total_length, total_time):
    try:
        conn = get_connection(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO routes (start_address, end_address, 
                       transport_mode, optimization_mode, 
                       distance_km, time_min)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (start, end, transport_mode, optimize_mode, total_length, total_time))

        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Маршрут успешно сохранён в базе данных.")

    except Exception as e:
        logger.error(f"Ошибка при сохранении маршрута в БД: {e}")


def test_connection():
    try:
        # Проверка подключения к master
        connection = get_connection()
        logger.info("Подключение к серверу SQL Server успешно.")
        connection.close()
        
        # Проверка подключения к базе данных route_history
        connection = get_connection(DB_NAME)
        cursor = connection.cursor()
        
        # Попытка выполнить простой запрос к таблице routes
        cursor.execute("SELECT TOP 1 * FROM Routes")
        row = cursor.fetchone()
        
        if row:
            logger.info(f"Подключение к базе {DB_NAME} успешно. Данные из таблицы routes:")
            # Получаем имена столбцов
            columns = [column[0] for column in cursor.description]
            # Выводим пары "имя_столбца: значение"
            for i, value in enumerate(row):
                logger.debug(f"{columns[i]}: {value}")
        else:
            logger.info(f"Подключение к базе {DB_NAME} успешно. Таблица routes существует, но пуста.")
            
        cursor.close()
        connection.close()
        return True
        
    except pyodbc.Error as err:
        logger.error(f"Ошибка при подключении к БД: {err}")
        return False
    
if __name__ == "__main__":
    test_connection()