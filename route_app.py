# route_app.py

# Стандартные библиотеки
import os
import random
import time
import webbrowser

# Сторонние библиотеки
import folium
import networkx as nx
import osmnx as ox
import tkinter as tk
import numpy as np
from geopy.geocoders import Nominatim
from sklearn.cluster import KMeans
from tkinter import messagebox, ttk

# Локальные модули
from app.database.db_utils import initialize_database, save_route_to_db
from app.routing.map_utils import load_or_create_map, get_edge_attributes
from app.configs.settings import CITIES

from loguru import logger

# Инициализация геолокатора
geolocator = Nominatim(user_agent="route_app")

# Кластеризация графа
def segment_graph(G, n_clusters=10):
    """Разбивает граф на регионы с помощью кластеризации узлов"""
    coords = np.array([[data["y"], data["x"]] for node, data in G.nodes(data=True)])
    node_ids = list(G.nodes)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42).fit(coords)
    labels = kmeans.labels_

    # Добавим информацию о регионе в атрибуты узлов
    for node_id, region in zip(node_ids, labels):
        G.nodes[node_id]["region"] = region

    return G, kmeans
# Поиск маршрута с учетом кластеризации
def find_regional_path(G, orig_node, dest_node, weight):
    orig_region = G.nodes[orig_node]["region"]
    dest_region = G.nodes[dest_node]["region"]

    if orig_region == dest_region:
        return nx.shortest_path(G, orig_node, dest_node, weight=weight)

    # Ищем узлы на границе регионов
    region_exits = [
        node for node in G.nodes
        if G.nodes[node]["region"] != orig_region and
           any(G.nodes[neighbor]["region"] == orig_region for neighbor in G.neighbors(node))
    ]

    best_path = None
    best_cost = float("inf")
    for exit_node in region_exits:
        try:
            path1 = nx.shortest_path(G, orig_node, exit_node, weight=weight)
            path2 = nx.shortest_path(G, exit_node, dest_node, weight=weight)
            full_path = path1[:-1] + path2
            cost = 0
            for u, v in zip(full_path[:-1], full_path[1:]):
                edge_data = G.get_edge_data(u, v)
                if isinstance(edge_data, dict):
                    first_key = next(iter(edge_data))
                    cost += edge_data[first_key].get(weight, 1)
                else:
                    cost += 1
            if cost < best_cost:
                best_cost = cost
                best_path = full_path
        except nx.NetworkXNoPath:
            continue

    return best_path


# Глобальный список для хранения объектов промежуточных точек
waypoints = []

def add_waypoint():
    """Добавляет поле для новой промежуточной точки маршрута"""
    # Индекс новой точки (начало и конец не считаются)
    idx = len(waypoints)
    
    # Создаем новую метку и поле ввода
    lbl = tk.Label(waypoints_frame, text=f"Точка {idx+1}:")
    lbl.grid(row=idx, column=0, sticky="w")
    
    entry = tk.Entry(waypoints_frame, width=40)
    entry.grid(row=idx, column=1, padx=5, pady=2)
    
    # Кнопка для удаления этой точки
    delete_btn = tk.Button(waypoints_frame, text="❌", command=lambda i=idx: remove_waypoint(i))
    delete_btn.grid(row=idx, column=2)
    
    # Добавляем объекты в список для дальнейшего доступа
    waypoints.append({"label": lbl, "entry": entry, "button": delete_btn, "index": idx})
    
    # Обновляем положение кнопки добавления точки
    add_waypoint_button.grid(row=len(waypoints)+1, column=0, columnspan=3)

def remove_waypoint(idx):
    """Удаляет промежуточную точку по индексу"""
    # Находим точку для удаления
    for i, wp in enumerate(waypoints):
        if wp["index"] == idx:
            # Удаляем виджеты
            wp["label"].destroy()
            wp["entry"].destroy()
            wp["button"].destroy()
            # Удаляем из списка
            waypoints.pop(i)
            break
    
    # Обновляем индексы и тексты оставшихся точек
    for i, wp in enumerate(waypoints):
        wp["index"] = i
        wp["label"].config(text=f"Точка {i+1}:")
    
    # Обновляем положение кнопки добавления
    add_waypoint_button.grid(row=len(waypoints)+1, column=0, columnspan=3)

def build_route():
    """Строит маршрут с учетом промежуточных точек с применением кластерного поиска"""
    start = start_entry.get()
    end = end_entry.get()
    travel_mode = transport_var.get()
    opt_mode = optimize_var.get()
    city_key = city_var.get()
    city_name = CITIES[city_key]

    logger.info(f"Начало построения маршрута: {start} -> {end}")
    logger.info(f"Город: {city_name}, Режим: {travel_mode}, Оптимизация: {opt_mode}")
    
    waypoint_addresses = [wp["entry"].get() for wp in waypoints if wp["entry"].get().strip()]
    logger.info(f"Промежуточные точки ({len(waypoint_addresses)}): {waypoint_addresses}")
    
    try:
        start_full = f"{start}, {city_name}"
        end_full = f"{end}, {city_name}"
        start_loc = geolocator.geocode(start_full)
        time.sleep(1)
        end_loc = geolocator.geocode(end_full)
        time.sleep(1)
        
        if not start_loc or not end_loc:
            raise ValueError("Невозможно определить координаты начальной или конечной точки")
        
        waypoint_locs = []
        for wp_addr in waypoint_addresses:
            wp_full = f"{wp_addr}, {city_name}"
            wp_loc = geolocator.geocode(wp_full)
            time.sleep(1)
            if not wp_loc:
                raise ValueError(f"Невозможно определить координаты точки: {wp_addr}")
            waypoint_locs.append(wp_loc)

        network_type = "drive" if travel_mode == "На машине" else "walk"
        G = load_or_create_map(network_type=network_type, city=city_name)
        logger.info(f"Карта загружена: {len(G.nodes)} узлов, {len(G.edges)} рёбер")

        orig_node = ox.nearest_nodes(G, start_loc.longitude, start_loc.latitude)
        dest_node = ox.nearest_nodes(G, end_loc.longitude, end_loc.latitude)
        waypoint_nodes = [ox.nearest_nodes(G, wp.longitude, wp.latitude) for wp in waypoint_locs]
        
        logger.info(f"Начальный узел: {orig_node}")
        logger.info(f"Конечный узел: {dest_node}")
        for i, node in enumerate(waypoint_nodes):
            logger.info(f"Узел точки {i+1}: {node}")

        for u, v, k, data in G.edges(keys=True, data=True):
            length_km = data.get("length", 1) / 1000
            if travel_mode == "Пешком":
                speed = random.uniform(4, 6)
            else:
                speed = random.choice([15, 30, 40, 50, 60])
            time_hr = length_km / speed
            G[u][v][k]["travel_time"] = time_hr * 60
            G[u][v][k]["speed"] = speed

        weight = "length" if opt_mode == "По расстоянию" else "travel_time"

        # Кластеризация графа
        logger.info("Сегментация графа на регионы")
        G_segmented, region_map = segment_graph(G)

        all_points = [orig_node] + waypoint_nodes + [dest_node]
        full_route = []
        total_length = 0
        total_time_min = 0

        for i in range(len(all_points) - 1):
            logger.info(f"Поиск маршрута: {all_points[i]} -> {all_points[i+1]}")
            segment_route = find_regional_path(
                G_segmented, all_points[i], all_points[i + 1], weight
            )
            if not segment_route or len(segment_route) < 2:
                raise ValueError("Не удалось построить маршрут между двумя точками")

            segment_length = sum(get_edge_attributes(G_segmented, segment_route, "length")) / 1000
            segment_time = sum(get_edge_attributes(G_segmented, segment_route, "travel_time"))
            total_length += segment_length
            total_time_min += segment_time

            if i == 0:
                full_route.extend(segment_route)
            else:
                full_route.extend(segment_route[1:])

        map_center = [start_loc.latitude, start_loc.longitude]
        folium_map = folium.Map(location=map_center, zoom_start=13)

        for u, v in zip(full_route[:-1], full_route[1:]):
            speed = G_segmented[u][v][0].get("speed", 0)
            if speed >= 40:
                color = "green"
            elif speed >= 20:
                color = "yellow"
            else:
                color = "red"

            coords = [(G_segmented.nodes[u]["y"], G_segmented.nodes[u]["x"]),
                      (G_segmented.nodes[v]["y"], G_segmented.nodes[v]["x"])]
            folium.PolyLine(coords, color=color, weight=5, opacity=0.7).add_to(folium_map)

        folium.Marker([start_loc.latitude, start_loc.longitude],
                      popup="Начало", icon=folium.Icon(color="green")).add_to(folium_map)
        for i, wp_loc in enumerate(waypoint_locs):
            folium.Marker([wp_loc.latitude, wp_loc.longitude],
                          popup=f"Точка {i+1}", icon=folium.Icon(color="blue")).add_to(folium_map)
        folium.Marker([end_loc.latitude, end_loc.longitude],
                      popup="Конец", icon=folium.Icon(color="red")).add_to(folium_map)

        map_filename = "map_route.html"
        folium_map.save(map_filename)
        webbrowser.open(f"file:///{os.path.abspath(map_filename)}")

        messagebox.showinfo(
            "Готово",
            f"Маршрут построен!\nДлина: {total_length:.2f} км\n"
            f"Время: {total_time_min:.1f} мин"
        )
        save_route_to_db(start, end, travel_mode, opt_mode, total_length, total_time_min)

    except Exception as e:
        messagebox.showerror("Ошибка", str(e))


def init_gui():
    """Инициализирует графический интерфейс приложения"""
    global root, waypoints_frame, start_entry, end_entry, city_var, transport_var, optimize_var, add_waypoint_button

     # Инициализация базы данных
    initialize_database()
    
    # Создание основного окна
    root = tk.Tk()
    root.title("Оптимальный маршрут")

    # Основной фрейм
    main_frame = tk.Frame(root, padx=10, pady=10)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Начальная и конечная точки
    tk.Label(main_frame, text="Начальный адрес:").grid(row=0, column=0, sticky="w")
    start_entry = tk.Entry(main_frame, width=40)
    start_entry.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(main_frame, text="Конечный адрес:").grid(row=1, column=0, sticky="w")
    end_entry = tk.Entry(main_frame, width=40)
    end_entry.grid(row=1, column=1, padx=5, pady=5)

    # Фрейм для промежуточных точек
    waypoints_frame = tk.LabelFrame(main_frame, text="Промежуточные точки")
    waypoints_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

    # Кнопка для добавления новой точки
    add_waypoint_button = tk.Button(waypoints_frame, text="+ Добавить точку", command=add_waypoint)
    add_waypoint_button.grid(row=0, column=0, columnspan=3, pady=5)

    # Настройки маршрута
    settings_frame = tk.LabelFrame(main_frame, text="Настройки маршрута")
    settings_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

    tk.Label(settings_frame, text="Город:").grid(row=0, column=0, sticky="w")
    city_var = ttk.Combobox(settings_frame, values=list(CITIES.keys()))
    city_var.current(0)
    city_var.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(settings_frame, text="Транспорт:").grid(row=1, column=0, sticky="w")
    transport_var = ttk.Combobox(settings_frame, values=["На машине", "Пешком"])
    transport_var.current(0)
    transport_var.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(settings_frame, text="Оптимизация:").grid(row=2, column=0, sticky="w")
    optimize_var = ttk.Combobox(settings_frame, values=["По расстоянию", "По времени"])
    optimize_var.current(0)
    optimize_var.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

    # Кнопка построения маршрута
    build_button = tk.Button(main_frame, text="Построить маршрут", command=build_route)
    build_button.grid(row=4, column=0, columnspan=2, pady=10)

    return root

def run_app():
    """Запускает приложение"""
    gui = init_gui()
    gui.mainloop()

if __name__ == "__main__":
    run_app()