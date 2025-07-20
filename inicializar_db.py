import sqlite3
conn = sqlite3.connect("datos_sensores.db")
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS sensores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_hora TEXT,
    temperatura REAL,
    humedad REAL,
    presion REAL,
    radiacion_uv REAL,
    calidad_aire REAL
)
''')
conn.commit()
conn.close()

print("? Base de datos creada e inicializada correctamente.")

