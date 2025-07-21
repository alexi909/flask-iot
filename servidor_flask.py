from flask import Flask, request, jsonify, render_template, send_file
from flask_httpauth import HTTPBasicAuth
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import csv
import os

app = Flask(__name__)
CORS(app)
auth = HTTPBasicAuth()

# Usuario de autenticación
usuarios = {
    "admin": generate_password_hash("admin123")
}

@auth.verify_password
def verify_password(username, password):
    if username in usuarios and check_password_hash(usuarios.get(username), password):
        return username

# Asegura que la tabla sensores exista
def crear_tabla_si_no_existe():
    conn = sqlite3.connect('datos_sensores.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sensores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_estacion TEXT,
            temperatura REAL,
            humedad REAL,
            presion REAL,
            calidad_aire INTEGER,
            radiacion_uv REAL,
            fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Ruta principal
@app.route('/')
def index():
    return "✅ Servidor Flask IoT activo. Usa /ver para visualizar los datos."

# Ruta para recibir datos del ESP32
@app.route('/datos_esp32', methods=['POST'])
def datos_esp32():
    data = request.get_json()

    nombre = data.get('nombre_estacion')
    temperatura = data.get('temperatura')
    humedad = data.get('humedad')
    presion = data.get('presion')
    calidad_aire = data.get('calidad_aire')
    radiacion_uv = data.get('radiacion_uv')

    if None in (nombre, temperatura, humedad, presion, calidad_aire, radiacion_uv):
        return jsonify({'error': '❌ Faltan datos'}), 400

    conn = sqlite3.connect('datos_sensores.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO sensores (nombre_estacion, temperatura, humedad, presion, calidad_aire, radiacion_uv)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (nombre, temperatura, humedad, presion, calidad_aire, radiacion_uv))
    conn.commit()
    conn.close()

    return jsonify({'mensaje': '✅ Datos recibidos correctamente'}), 200

# Ruta para visualizar datos
@app.route('/ver')
@auth.login_required
def ver_datos():
    conn = sqlite3.connect('datos_sensores.db')
    c = conn.cursor()
    c.execute('SELECT * FROM sensores ORDER BY id DESC LIMIT 100')
    datos = c.fetchall()
    conn.close()

    datos_recibidos = []
    for fila in datos:
        datos_recibidos.append({
            'id': fila[0],
            'nombre_estacion': fila[1],
            'temperatura': fila[2],
            'humedad': fila[3],
            'presion': fila[4],
            'calidad_aire': fila[5],
            'radiacion_uv': fila[6],
            'fecha_hora': fila[7]
        })

    return render_template('ver_datos.html', datos=datos_recibidos)

# Ruta para exportar CSV
@app.route('/exportar_csv')
@auth.login_required
def exportar_csv():
    conn = sqlite3.connect('datos_sensores.db')
    c = conn.cursor()
    c.execute('SELECT * FROM sensores')
    datos = c.fetchall()
    conn.close()

    csv_path = 'datos_exportados.csv'
    with open(csv_path, 'w', newline='') as archivo_csv:
        writer = csv.writer(archivo_csv)
        writer.writerow(['ID', 'Nombre Estación', 'Temperatura', 'Humedad', 'Presión', 'Calidad Aire', 'Radiación UV', 'Fecha y Hora'])
        for fila in datos:
            writer.writerow(fila)

    response = send_file(csv_path, as_attachment=True)

    # Opcional: eliminar el archivo después de enviar
    @response.call_on_close
    def limpiar_archivo():
        if os.path.exists(csv_path):
            os.remove(csv_path)

    return response

# Ruta para eliminar todos los datos de la tabla
@app.route('/eliminar')
@auth.login_required
def eliminar_datos():
    conn = sqlite3.connect('datos_sensores.db')
    c = conn.cursor()
    c.execute('DELETE FROM sensores')
    conn.commit()
    conn.close()
    return render_template('mensaje.html', mensaje="? Todos los datos han sido eliminados correctamente.")

# Iniciar servidor Flask
if __name__ == '__main__':
    crear_tabla_si_no_existe()
    app.run(host='0.0.0.0', port=5000, debug=True)
