# tests/test_main.py
import unittest
import sys
import os

# Добавляем корень проекта в путь импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Импортируем тестовые модули
from tests.test_routing import TestRouting
from tests.test_database import TestDatabase
from tests.test_gui import TestGUI

def load_all_tests():
    """Формирует и возвращает полный набор тестов."""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestRouting))
    suite.addTest(unittest.makeSuite(TestDatabase))
    suite.addTest(unittest.makeSuite(TestGUI))
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(load_all_tests())
