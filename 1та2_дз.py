import psycopg2
import folium

def read_coordinates_from_file(file_path):
    coordinates = []
    with open(file_path, 'r', encoding='utf-8') as file:
        data = file.read()
        # координати у форматі [longitude, latitude]
        data = data.replace('[', '').replace(']', '').strip()
        pairs = data.split(', ')
        for i in range(0, len(pairs), 2):
            lon = float(pairs[i])
            lat = float(pairs[i + 1])
            coordinates.append((lat, lon))
    return coordinates

# шлях до вашого файлу
file_path = r'C:\Users\User_\SA\тестове\vodafonе_дз\coord_border_Uk.txt'

# зчитування координат
coordinates = read_coordinates_from_file(file_path)

def create_database_if_not_exists(connection_params, database_name):
    conn = psycopg2.connect(**connection_params)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(f"SELECT 1 FROM pg_database WHERE datname = %s;", (database_name,))
    if not cur.fetchone():
        cur.execute(f"CREATE DATABASE {database_name};")
        print(f"База даних '{database_name}' створена.")
    else:
        print(f"База даних '{database_name}' вже існує.")
    cur.close()
    conn.close()

# Параметри підключення
connection_params = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5432"
}

database_name = "coordinates_uk_db"

# Створення бази даних, якщо вона не існує
create_database_if_not_exists(connection_params, database_name)

# Підключення до нової бази даних
conn = psycopg2.connect(
    dbname=database_name,
    user="postgres",
    password="postgres",
    host="localhost",
    port="5432"
)

cur = conn.cursor()

# Підключення PostGIS розширення
cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
conn.commit()
print("PostGIS розширення підключено.")


# Видалення старої таблиці, якщо вона існує
cur.execute("DROP TABLE IF EXISTS ukraine_borders;")
conn.commit()


cur.execute("""
CREATE TABLE IF NOT EXISTS ukraine_borders (
    id SERIAL PRIMARY KEY,
    geom GEOMETRY(Point, 4326)
);
""")
conn.commit()
print("Таблиця 'ukraine_borders' створена .")

# Додавання даних
for lat, lon in coordinates:
    cur.execute("""
    INSERT INTO ukraine_borders (geom)
    VALUES (ST_SetSRID(ST_MakePoint(%s, %s), 4326));
    """, (lon, lat))
conn.commit()
print("Координати додано до таблиці.")

# Витягування всіх точок з таблиці для побудови карти
cur.execute("""
SELECT ST_X(geom) AS lon, ST_Y(geom) AS lat 
FROM ukraine_borders;
""")
coordinates_from_db = cur.fetchall()

# Закриття з'єднання з базою даних
cur.close()
conn.close()

# Створення карти з центруванням на середину координат
if coordinates_from_db:
    map_center = [
        sum([coord[1] for coord in coordinates_from_db]) / len(coordinates_from_db),
        sum([coord[0] for coord in coordinates_from_db]) / len(coordinates_from_db)
    ]

    my_map = folium.Map(location=map_center, zoom_start=7)

    # Додавання полігону на карту
    folium.Polygon(
        locations=[(lat, lon) for lon, lat in coordinates_from_db],
        color='blue',
        fill=True,
        fill_color='blue',
        fill_opacity=0.4
    ).add_to(my_map)

    my_map.save("ukraine_borders_map.html")
    print("Карта збережена у файл 'ukraine_borders_map.html'. Відкрийте файл у браузері для перегляду.")
else:
    print("Таблиця порожня, карта не створена.")
