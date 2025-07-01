# map_utils.py

import os
import osmnx as ox
from app.configs.settings import GRAPHML_FILENAME_DRIVE, GRAPHML_FILENAME_WALK

ox.settings.use_cache = True

from loguru import logger


def load_or_create_map(network_type="drive", city="Краснодар, Россия"):
    # Имя файла теперь должно включать и город для разделения кэшей
    city_slug = city.split(",")[0].strip().lower().replace(" ", "_")
    filename = f"{city_slug}_{GRAPHML_FILENAME_DRIVE}" if network_type == "drive" else f"{city_slug}_{GRAPHML_FILENAME_WALK}"
    
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    file_path = os.path.join(data_dir, filename)

    if os.path.exists(file_path):
        logger.info(f"Загружаем карту из файла: {file_path}")
        return ox.load_graphml(file_path)
    else:
        logger.info(f"Загрузка новой карты из OSM для {city}...")
        G = ox.graph_from_place(city, network_type=network_type)
        ox.save_graphml(G, file_path)
        return G
    
def get_edge_attributes(G, route, attribute):
    """
    Получает атрибуты рёбер графа для заданного маршрута.
    
    Args:
        G: Граф OSMnx
        route: Список узлов, составляющих маршрут
        attribute: Название атрибута для извлечения
        
    Returns:
        Список значений атрибута для каждого ребра в маршруте
    """
    return [G[u][v][0].get(attribute, 0) for u, v in zip(route[:-1], route[1:])]