from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import datetime
import csv
import io

app = Flask(__name__)
CORS(app)
auth = HTTPBasicAuth()

# Usuario y contraseña
users = {
    "admin": generate_password_hash("12345")
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username

# Crear la base de datos
DB_FILE = "sensores.db"

def init_db():
    with sqlite3.connect(DB_FILE) as con:
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS datos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_hora TEXT,
                temperatura REAL,
                humedad REAL,
                presion REAL,
                radiacion_uv REAL,
                calidad_aire INTEGER
            )
        """)
        con.commit()

init_db()

@app.route('/')
@auth.login_required
def index():
    return render_template('index.html')

@app.route('/ver_datos')
@auth.login_required
def ver_datos():
    with sqlite3.connect(DB_FILE) as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM datos ORDER BY id ASC")
        datos = cur.fetchall()
    return render_template('ver_datos.html', datos=datos)

@app.route('/ver_datos_json')
def ver_datos_json():
    with sqlite3.connect(DB_FILE) as con:
        cur = con.cursor()
        cur.execute("SELECT fecha_hora, temperatura, humedad, presion, radiacion_uv, calidad_aire FROM datos")
        filas = cur.fetchall()
    columnas = ['fecha_hora', 'temperatura', 'humedad', 'presion', 'radiacion_uv', 'calidad_aire']
    return jsonify([dict(zip(columnas, fila)) for fila in filas])

@app.route('/api/datos')
def api_datos():
    with sqlite3.connect(DB_FILE) as con:
        cur = con.cursor()
        cur.execute("SELECT fecha_hora, temperatura, humedad, presion, radiacion_uv, calidad_aire FROM datos ORDER BY id DESC LIMIT 1")
        fila = cur.fetchone()
    if fila:
        columnas = ['fecha_hora', 'temperatura', 'humedad', 'presion', 'radiacion_uv', 'calidad_aire']
        return jsonify(dict(zip(columnas, fila)))
    return jsonify({})

@app.route('/datos_esp32', methods=['POST'])
def recibir_datos():
    try:
        data = request.get_json()
        fecha_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(DB_FILE) as con:
            cur = con.cursor()
            cur.execute("""
                INSERT INTO datos (fecha_hora, temperatura, humedad, presion, radiacion_uv, calidad_aire)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                fecha_hora,
                data.get('temperatura'),
                data.get('humedad'),
                data.get('presion'),
                data.get('radiacion_uv'),
                data.get('calidad_aire')
            ))
            con.commit()
        print(f"Datos guardados: {data}")
        return jsonify({"mensaje": "Datos guardados correctamente"}), 200
    except Exception as e:
        print(f"Error al guardar datos: {e}")
        return jsonify({"error": str(e)}), 400

@app.route('/exportar')
@auth.login_required
def exportar():
    with sqlite3.connect(DB_FILE) as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM datos")
        rows = cur.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Fecha/Hora', 'Temperatura', 'Humedad', 'Presion', 'Radiacion UV', 'Calidad Aire'])
    writer.writerows(rows)

    output.seek(0)
    return send_file(
        io.BytesIO(output.read().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='datos_exportados.csv'
    )

@app.route('/eliminar', methods=['POST'])
@auth.login_required
def eliminar_datos():
    with sqlite3.connect(DB_FILE) as con:
        cur = con.cursor()
        cur.execute("DELETE FROM datos")
        con.commit()
    return redirect(url_for('ver_datos'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

