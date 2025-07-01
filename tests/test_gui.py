# tests/test_gui.py
import unittest
import os
import sys
import networkx as nx
from unittest.mock import patch, MagicMock
import tkinter as tk
from tkinter import messagebox

# Добавление корневого каталога проекта в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import route_app
from app.configs.settings import CITIES

class TestGUI(unittest.TestCase):
    """Тесты для графического интерфейса пользователя."""

    def setUp(self):
        """Инициализация окна и тестовых элементов перед каждым тестом."""
        # Очистка глобальных переменных
        route_app.waypoints = []
        
        # Создание тестовых элементов
        self.root = tk.Tk()
        self.start_entry = tk.Entry(self.root)
        self.end_entry = tk.Entry(self.root)
        self.city_var = tk.StringVar(value=list(CITIES.keys())[0])
        self.transport_var = tk.StringVar(value="На машине")
        self.optimize_var = tk.StringVar(value="По расстоянию")
        self.waypoints_frame = tk.LabelFrame(self.root, text="Промежуточные точки")
        
        # Установка глобальных переменных для тестов
        route_app.root = self.root
        route_app.start_entry = self.start_entry
        route_app.end_entry = self.end_entry
        route_app.city_var = self.city_var
        route_app.transport_var = self.transport_var
        route_app.optimize_var = self.optimize_var
        route_app.waypoints_frame = self.waypoints_frame
        route_app.add_waypoint_button = tk.Button(self.waypoints_frame, text="+ Добавить точку")

    def tearDown(self):
        """Закрытие окна после каждого теста."""
        self.root.destroy()
        route_app.waypoints = []

    @patch('route_app.build_route')
    def test_build_button_click(self, mock_build_route):
        """Тест вызова построения маршрута при нажатии кнопки."""
        build_button = tk.Button(self.root, text="Построить маршрут", command=mock_build_route)
        build_button.invoke()
        mock_build_route.assert_called_once()

    @patch('geopy.geocoders.Nominatim.geocode')
    @patch('route_app.load_or_create_map')
    @patch('route_app.save_route_to_db')
    @patch('tkinter.messagebox.showinfo')
    @patch('route_app.webbrowser.open')
    def test_build_route_integration(self, mock_webbrowser, mock_showinfo, mock_save,
                                    mock_load_map, mock_geocode):
        """Интеграционный тест полного построения маршрута."""

        # Настройка интерфейса
        route_app.start_entry = self.start_entry
        route_app.end_entry = self.end_entry
        route_app.city_var = self.city_var
        route_app.transport_var = self.transport_var
        route_app.optimize_var = self.optimize_var
        route_app.messagebox = messagebox

        self.start_entry.insert(0, "Красная площадь")
        self.end_entry.insert(0, "Кремль")

        # Моки геокодирования
        mock_start_loc = MagicMock(latitude=55.753, longitude=37.621)
        mock_end_loc = MagicMock(latitude=55.752, longitude=37.618)
        mock_geocode.side_effect = [mock_start_loc, mock_end_loc]

        # Настройка реального графа
        G = nx.MultiDiGraph()
        G.add_node(1, x=37.621, y=55.753)
        G.add_node(2, x=37.618, y=55.752)
        G.add_edge(1, 2, length=1000, speed=40, travel_time=1.5)
        G.graph['crs'] = 'EPSG:4326'

        mock_load_map.return_value = G

        with patch('route_app.nx.shortest_path', return_value=[1, 2]) as mock_shortest_path, \
            patch('folium.Map') as mock_map, \
            patch('folium.Marker'), \
            patch('folium.PolyLine'), \
            patch('folium.Map.save'):
            
            mock_map_instance = MagicMock()
            mock_map.return_value = mock_map_instance

            route_app.build_route()

            mock_geocode.assert_called()
            mock_load_map.assert_called_once()
            mock_shortest_path.assert_called_once()
            mock_showinfo.assert_called_once()
            mock_save.assert_called_once()
            mock_webbrowser.assert_called_once()

    @patch('route_app.add_waypoint')
    def test_add_waypoint_button(self, mock_add_waypoint):
        """Тест добавления промежуточной точки."""
        add_button = tk.Button(self.root, text="+ Добавить точку", command=mock_add_waypoint)
        add_button.invoke()
        mock_add_waypoint.assert_called_once()

    def test_add_waypoint_function(self):
        """Проверка функциональности добавления точки."""
        route_app.waypoints_frame = self.waypoints_frame
        route_app.add_waypoint_button = tk.Button(self.waypoints_frame, text="+ Добавить точку")
        self.assertEqual(len(route_app.waypoints), 0)

        route_app.add_waypoint()

        self.assertEqual(len(route_app.waypoints), 1)
        self.assertEqual(route_app.waypoints[0]["index"], 0)
        self.assertIsInstance(route_app.waypoints[0]["label"], tk.Label)
        self.assertIsInstance(route_app.waypoints[0]["entry"], tk.Entry)
        self.assertIsInstance(route_app.waypoints[0]["button"], tk.Button)

    def test_remove_waypoint_function(self):
        """Проверка удаления промежуточной точки."""
        route_app.waypoints_frame = self.waypoints_frame
        route_app.add_waypoint_button = tk.Button(self.waypoints_frame, text="+ Добавить точку")

        route_app.add_waypoint()
        route_app.add_waypoint()
        self.assertEqual(len(route_app.waypoints), 2)

        route_app.remove_waypoint(0)

        self.assertEqual(len(route_app.waypoints), 1)
        self.assertEqual(route_app.waypoints[0]["index"], 0)
        self.assertEqual(route_app.waypoints[0]["label"].cget("text"), "Точка 1:")

if __name__ == '__main__':
    unittest.main()
