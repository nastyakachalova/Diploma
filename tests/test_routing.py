# tests/test_routing.py
import unittest
import os
import sys
import networkx as nx
from unittest.mock import patch, MagicMock

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.routing.map_utils import load_or_create_map, get_edge_attributes

class TestRouting(unittest.TestCase):
    """Тесты для функций маршрутизации."""

    def setUp(self):
        """Создание тестового графа перед каждым тестом."""
        self.test_graph = nx.MultiDiGraph()
        self.test_graph.add_node(1, x=30.0, y=45.0)
        self.test_graph.add_node(2, x=30.1, y=45.1)
        self.test_graph.add_node(3, x=30.2, y=45.2)
        self.test_graph.add_edge(1, 2, 0, length=1000, speed=40)
        self.test_graph.add_edge(2, 3, 0, length=1500, speed=60)

    def test_get_edge_attributes(self):
        """Тест получения значений атрибутов ребер графа."""
        route = [1, 2, 3]

        # Проверка извлечения длин рёбер
        lengths = get_edge_attributes(self.test_graph, route, 'length')
        self.assertEqual(lengths, [1000, 1500])

        # Проверка извлечения скоростей рёбер
        speeds = get_edge_attributes(self.test_graph, route, 'speed')
        self.assertEqual(speeds, [40, 60])

        # Проверка обработки отсутствующих атрибутов (должен вернуть 0)
        missing = get_edge_attributes(self.test_graph, route, 'non_existent')
        self.assertEqual(missing, [0, 0])

    @patch('osmnx.load_graphml')
    @patch('osmnx.save_graphml')
    @patch('osmnx.graph_from_place')
    def test_load_or_create_map_existing(self, mock_graph_from_place, mock_save_graphml, mock_load_graphml):
        """Тест загрузки карты из файла, если файл существует."""
        with patch('os.path.exists', return_value=True):
            mock_load_graphml.return_value = self.test_graph
            result = load_or_create_map(network_type="drive", city="Москва, Россия")

            mock_load_graphml.assert_called_once()
            mock_graph_from_place.assert_not_called()
            self.assertEqual(result, self.test_graph)

    @patch('osmnx.load_graphml')
    @patch('osmnx.save_graphml')
    @patch('osmnx.graph_from_place')
    def test_load_or_create_map_new(self, mock_graph_from_place, mock_save_graphml, mock_load_graphml):
        """Тест создания новой карты, если файл отсутствует."""
        with patch('os.path.exists', return_value=False):
            mock_graph_from_place.return_value = self.test_graph
            result = load_or_create_map(network_type="drive", city="Москва, Россия")

            mock_graph_from_place.assert_called_once()
            mock_save_graphml.assert_called_once()
            self.assertEqual(result, self.test_graph)

if __name__ == '__main__':
    unittest.main()
