# tests/test_database.py
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import pyodbc
from loguru import logger

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from app.database.db_utils import (
    get_connection, 
    initialize_database, 
    save_route_to_db, test_connection,)
from app.configs.settings import DB_CONFIG

DB_NAME = DB_CONFIG["database"]

class TestDatabase(unittest.TestCase):
    """Тесты для функций работы с базой данных."""

    @patch('pyodbc.connect')
    def test_get_connection(self, mock_connect):
        """Тест подключения к базе данных."""
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection

        # Проверка подключения к master
        get_connection()
        mock_connect.assert_called_once()
        self.assertIn('DATABASE=master', mock_connect.call_args[0][0])

        # Проверка подключения к пользовательской базе
        mock_connect.reset_mock()
        get_connection('test_db')
        mock_connect.assert_called_once()
        self.assertIn('DATABASE=test_db', mock_connect.call_args[0][0])

    @patch('app.database.db_utils.get_connection')
    def test_initialize_database(self, mock_get_connection):
        """Тест создания структуры базы данных."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        initialize_database()

        self.assertEqual(mock_get_connection.call_count, 2)
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()
        mock_cursor.close.assert_called()
        mock_conn.close.assert_called()

    @patch('app.database.db_utils.get_connection')
    def test_save_route_to_db(self, mock_get_connection):
        """Тест сохранения маршрута в базу данных."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        start, end, mode, optimize, length, time = "A", "B", "Car", "Time", 5.0, 10.0

        save_route_to_db(start, end, mode, optimize, length, time)

        mock_get_connection.assert_called_once_with(DB_NAME)
        mock_cursor.execute.assert_called_once()
        self.assertEqual(mock_cursor.execute.call_args[0][1], (start, end, mode, optimize, length, time))
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('app.database.db_utils.get_connection')
    def test_test_connection_success(self, mock_get_connection):
        """Тест успешного подключения к базе данных."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"id": 1}
        mock_cursor.description = [("id", ), ("start_address", )]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        result = test_connection()

        self.assertTrue(result)
        self.assertEqual(mock_get_connection.call_count, 2)
        mock_cursor.execute.assert_called_once_with("SELECT TOP 1 * FROM Routes")
        mock_cursor.close.assert_called()
        mock_conn.close.assert_called()

    @patch('app.database.db_utils.get_connection')
    def test_test_connection_failure(self, mock_get_connection):
        """Тест обработки ошибки подключения."""
        mock_get_connection.side_effect = pyodbc.Error("Ошибка подключения")
        result = test_connection()
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
