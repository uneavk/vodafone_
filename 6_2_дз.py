import math
import psycopg2


def create_sector_polygon(center_lat, center_lon, azimuth, spread, radius_km):
    """
    Створює WKT-репрезентацію сектора.

    :param center_lat: широта центру сектора.
    :param center_lon: довгота центру сектора.
    :param azimuth: центральний азимут сектора (в градусах).
    :param spread: кут розкриття сектора (в градусах).
    :param radius_km: радіус сектора в км.
    :return: WKT-полігон сектора.
    """
    points = [(center_lon, center_lat)]
    for angle in range(-spread // 2, spread // 2 + 1, 1):  # Крок у  градусах
        angle_rad = math.radians(azimuth + angle)
        d_lat = radius_km / 6371 * math.cos(angle_rad) * (180 / math.pi)
        d_lon = radius_km / (6371 * math.cos(math.radians(center_lat))) * math.sin(angle_rad) * (180 / math.pi)
        points.append((center_lon + d_lon, center_lat + d_lat))
    points.append((center_lon, center_lat))  # Замикання сектора
    return f"POLYGON(({','.join([f'{lon} {lat}' for lon, lat in points])}))"


# Підключення до бази даних
conn = psycopg2.connect(
    dbname="coordinates_uk_db",
    user="postgres",
    password="postgres",
    host="localhost",
    port="5432"
)

cur = conn.cursor()

# Створення таблиці для збереження результатів
cur.execute("""
    CREATE TABLE IF NOT EXISTS sector_50 (
        id SERIAL PRIMARY KEY,
        sector_id INTEGER NOT NULL,
        point_id INTEGER NOT NULL
    );
""")
conn.commit()

# Отримання всіх точок із таблиці intersection
cur.execute("""
    SELECT id, ST_Y(geom) AS lat, ST_X(geom) AS lon 
    FROM square_vertices_10;
""")
intersection_points = cur.fetchall()

# Підготовка секторів і перетинів
radius_km = 50
spread = 60
azimuths = [0, 120, 240]

sectors = []
for point_id, center_lat, center_lon in intersection_points:
    for azimuth in azimuths:
        sector_polygon = create_sector_polygon(center_lat, center_lon, azimuth, spread, radius_km)
        sectors.append((point_id, azimuth, sector_polygon))

# Перевірка перетинів усіх секторів із точками
for sector in sectors:
    point_id, azimuth, sector_polygon = sector
    sector_id = int(f"{point_id}{azimuth}")  # Унікальний ідентифікатор сектора
  # id для сектора складається з точки з якої він виходить та азимута

    # Запит до бази даних для перевірки всіх точок
    cur.execute("""
        INSERT INTO sector_50 (sector_id, point_id)
        SELECT %s, i.id
        FROM square_vertices_10 i
        WHERE ST_Contains(ST_GeomFromText(%s, 4326), i.geom)
          AND i.id != %s;
    """, (sector_id, sector_polygon, point_id))

conn.commit()

print("Перетини секторів з вершинами обчислено та збережено.")
cur.close()
conn.close()
