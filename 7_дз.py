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

    for angle in range(-spread // 2, spread // 2 + 1, 1):
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

# Отримання точок з таблиці intersection
cur.execute("""
SELECT diagonal_id, vertical_id, ST_X(geom) AS lon, ST_Y(geom) AS lat
FROM square_vertices_10
ORDER BY diagonal_id, vertical_id;
""")
points = cur.fetchall()

if not points:
    print("Таблиця square_vertices_10 порожня!")
    exit()

# Групування точок для створення квадратів
grid = {}
for diagonal_id, vertical_id, lon, lat in points:
    if diagonal_id not in grid:
        grid[diagonal_id] = {}
    grid[diagonal_id][vertical_id] = (lat, lon)

# Визначення центру карти
map_center = [
    sum([point[3] for point in points]) / len(points),  # Середня широта
    sum([point[2] for point in points]) / len(points)   # Середня довгота
]

# Створення карти
combined_map = folium.Map(location=map_center, zoom_start=7)

# Малювання квадратів
for diagonal_id in sorted(grid.keys()):
    for vertical_id in sorted(grid[diagonal_id].keys()):
        if (diagonal_id + 1 in grid and
                vertical_id in grid[diagonal_id + 1] and
                vertical_id + 1 in grid[diagonal_id] and
                vertical_id + 1 in grid[diagonal_id + 1]):
            sw = grid[diagonal_id][vertical_id]
            se = grid[diagonal_id + 1][vertical_id]
            ne = grid[diagonal_id + 1][vertical_id + 1]
            nw = grid[diagonal_id][vertical_id + 1]

            square_coords = [sw, se, ne, nw, sw]
            folium.PolyLine(square_coords, color='orange', weight=7, opacity=0.9).add_to(combined_map)

# Додавання секторів
for diagonal_id in grid:
    for vertical_id in grid[diagonal_id]:
        center_point = grid[diagonal_id][vertical_id]
        add_sector(combined_map, center_point, azimuth=0, spread=60, radius=50000, color="red")
        add_sector(combined_map, center_point, azimuth=120, spread=60, radius=50000, color="green")
        add_sector(combined_map, center_point, azimuth=240, spread=60, radius=50000, color="blue")


# Збереження карти у файл
combined_map.save("combined_map.html")
print("Карта збережена у файл 'combined_map.html'. Відкрийте файл у браузері для перегляду.")

# Закриття з'єднання
cur.close()
conn.close()
