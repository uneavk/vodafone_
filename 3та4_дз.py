import psycopg2
import math
# Підключення до бази даних
conn = psycopg2.connect(
    dbname="coordinates_uk_db",
    user="postgres",
    password="postgres",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# Видалення старої таблиці, якщо вона існує
cur.execute("DROP TABLE IF EXISTS square_vertices_10;")
conn.commit()

# Створення таблиці для зберігання вершин із стовпцями
cur.execute("""
CREATE TABLE square_vertices_10 (
    id SERIAL PRIMARY KEY,
    diagonal_id INTEGER NOT NULL,
    vertical_id INTEGER NOT NULL,
    geom GEOMETRY(Point, 4326)
);
""")
conn.commit()
print("Таблиця 'square_vertices_10' створена.")

# Витягування координат меж полігону
cur.execute("""
SELECT ST_X(geom) AS lon, ST_Y(geom) AS lat 
FROM ukraine_borders;
""")
coordinates_from_db = cur.fetchall()

if not coordinates_from_db:
    print("Таблиця меж України порожня!")
    cur.close()
    conn.close()
    exit()
# Створення таблиці для збереження полігону України.Його можна будувати кожен раз "на ходу", але це дуже сповільнить код
cur.execute("DROP TABLE IF EXISTS ukraine_polygon;")
conn.commit()

cur.execute("""
CREATE TABLE ukraine_polygon (
    id SERIAL PRIMARY KEY,
    geom GEOMETRY(Polygon, 4326)
);
""")
conn.commit()
print("Таблиця 'ukraine_polygon' створена.")

# Створення полігону на основі точок
polygon_coordinates = [(lon, lat) for lon, lat in coordinates_from_db]
polygon_wkt = f"POLYGON(({', '.join(f'{lon} {lat}' for lon, lat in polygon_coordinates)}))"

cur.execute("""
INSERT INTO ukraine_polygon (geom)
VALUES (ST_SetSRID(ST_GeomFromText(%s), 4326));
""", (polygon_wkt,))
conn.commit()
print("Полігон України додано до таблиці 'ukraine_polygon'.")

# Визначення меж полігону, для "прямокутника"
min_lat = min(coord[1] for coord in coordinates_from_db)
max_lat = max(coord[1] for coord in coordinates_from_db)
min_lon = min(coord[0] for coord in coordinates_from_db)
max_lon = max(coord[0] for coord in coordinates_from_db)

degree_per_km_lat = 10 / (111 * 1.5)  # Для широти. (щоб квадрати були по 1 км^2, змінити 10 на 1
degree_per_km_lon = 10 / 111  # Для довготи .(щоб квадрати були по 1 км^2, змінити 10 на 1

lat_steps = math.ceil((max_lat - min_lat) / degree_per_km_lat)
lon_steps = math.ceil((max_lon - min_lon) / degree_per_km_lon)

# Масив точок перетину
intersection = []

# Генерація точок і перевірка на входження в полігон
for i in range(lat_steps + 1):
    current_lat = min_lat + i * degree_per_km_lat
    for j in range(lon_steps + 1):
        current_lon = min_lon + j * degree_per_km_lon

        # Перевірка, чи входить точка у полігон України
        cur.execute("""
        SELECT ST_Contains(
            (SELECT geom FROM ukraine_polygon LIMIT 1),
            ST_SetSRID(ST_MakePoint(%s, %s), 4326)
        );
        """, (current_lon, current_lat))

        is_inside = cur.fetchone()[0]
        if is_inside:
            intersection.append((i, j, current_lat, current_lon))

# Вставка точок у таблицю
for i, j, lat, lon in intersection:
    cur.execute("""
    INSERT INTO square_vertices_10 (diagonal_id, vertical_id, geom)
    VALUES (%s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326));
    """, (i, j, lon, lat))
conn.commit()

# Підсумок
print(f"У базу даних додано {len(intersection)} точок, які входять у межі полігону України.")

# Закриття з'єднання
cur.close()
conn.close()
