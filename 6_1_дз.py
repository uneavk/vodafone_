import math
import folium
import psycopg2


def add_sector(map_object, center, azimuth, spread, radius, color):
    """
    Додає сектор на карту.

    :param map_object: folium.Map об'єкт.
    :param center: (lat, lon) центральна точка сектора.
    :param azimuth: центральний азимут сектора в градусах.
    :param spread: кут розкриття сектора в градусах.
    :param radius: радіус сектора в метрах.
    :param color: колір сектора.
    """
    lat, lon = center
    points = [center]

    for angle in range(-spread // 2, spread // 2 + 1, 1):  # Крок у градусах
        angle_rad = math.radians(azimuth + angle)
        d_lat = (radius / 1000) / 6371 * math.cos(angle_rad) * (180 / math.pi)
        d_lon = (radius / 1000) / (6371 * math.cos(math.radians(lat))) * math.sin(angle_rad) * (180 / math.pi)
        points.append((lat + d_lat, lon + d_lon))

    points.append(center)  # Замкнути сектор
    folium.Polygon(points, color=color, fill=True, fill_opacity=0.01).add_to(map_object)


# Підключення до бази даних
conn = psycopg2.connect(
    dbname="coordinates_uk_db",
    user="postgres",
    password="postgres",
    host="localhost",
    port="5432"
)

cur = conn.cursor()

# Отримання всіх точок з таблиці intersection
cur.execute("""
    SELECT ST_Y(geom) AS lat, ST_X(geom) AS lon 
    FROM square_vertices_10;
""")
intersection_points = cur.fetchall()

# Закриття з'єднання
cur.close()
conn.close()


if intersection_points:
    # Визначення центру карти на основі першої точки
    map_center = [intersection_points[0][0], intersection_points[0][1]]
    sector_map = folium.Map(location=map_center, zoom_start=13)

    # Додавання секторів
    for lat, lon in intersection_points:
        center_point = (lat, lon)               #беру саме 50 км для радіусу щоб було співвідношення 1/5
        add_sector(sector_map, center_point, azimuth=0, spread=60, radius=50000, color="red") #щоб були 5км, замінюємо на 5000
        add_sector(sector_map, center_point, azimuth=120, spread=60, radius=50000, color="green")
        add_sector(sector_map, center_point, azimuth=240, spread=60, radius=50000, color="blue")

    # Збереження карти у файл
    sector_map.save("map_with_sectors.html")
    print("Карта з секторами збережена у файл 'map_with_sectors.html'.")
else:
    print("Таблиця 'square_vertices_10' порожня.")
