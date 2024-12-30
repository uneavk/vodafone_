import psycopg2
import folium

# Підключення до бази даних
conn = psycopg2.connect(
    dbname="coordinates_uk_db",
    user="postgres",
    password="postgres",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# Витягування точок із таблиці intersections
cur.execute("""
SELECT diagonal_id, vertical_id, ST_X(geom) AS lon, ST_Y(geom) AS lat
FROM square_vertices_10
ORDER BY diagonal_id, vertical_id;
""")
points = cur.fetchall()

# Перевірка, чи є дані
if not points:
    print("Таблиця square_vertices_10 порожня!")
    exit()

# Групування точок за diagonal_id та vertical_id
grid = {}
for diagonal_id, vertical_id, lon, lat in points:
    if diagonal_id not in grid:
        grid[diagonal_id] = {}
    grid[diagonal_id][vertical_id] = (lat, lon)

# Створення карти
map_center = [
    sum([point[3] for point in points]) / len(points),  # Середня широта
    sum([point[2] for point in points]) / len(points)  # Середня довгота
]
my_map = folium.Map(location=map_center, zoom_start=7)

# Малювання квадратів
for diagonal_id in sorted(grid.keys()):
    for vertical_id in sorted(grid[diagonal_id].keys()):
        # Перевірка наявності сусідів для формування квадрату
        if (diagonal_id + 1 in grid and
                vertical_id in grid[diagonal_id + 1] and
                vertical_id + 1 in grid[diagonal_id] and
                vertical_id + 1 in grid[diagonal_id + 1]):
            # Координати вершини квадрату
            sw = grid[diagonal_id][vertical_id]
            se = grid[diagonal_id + 1][vertical_id]
            ne = grid[diagonal_id + 1][vertical_id + 1]
            nw = grid[diagonal_id][vertical_id + 1]

            # Формування квадрату
            square_coords = [sw, se, ne, nw, sw]
            folium.PolyLine(square_coords, color='blue', weight=2, opacity=0.6).add_to(my_map)

# Збереження карти у файл
my_map.save("ukraine_grid_map.html")
print("Карта збережена у файл 'ukraine_grid_map.html'. Відкрийте файл у браузері для перегляду.")

# Закриття з'єднання з базою даних
cur.close()
conn.close()
