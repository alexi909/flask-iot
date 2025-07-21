from flask import Flask, render_template, request, jsonify, g
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'clave_secreta_actualizada'
app.config['DATABASE'] = 'data.db'
app.config['TEMPLATES_AUTO_RELOAD'] = True

auth = HTTPBasicAuth()

users = {
    "admin": generate_password_hash("admin123")
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username
    return None

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                temperature REAL NOT NULL,
                humidity REAL NOT NULL,
                pressure REAL NOT NULL,
                light REAL NOT NULL,
                air_quality_raw INTEGER NOT NULL,
                air_quality TEXT NOT NULL,
                timestamp DATETIME NOT NULL
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON sensor_data (timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_device ON sensor_data (device_id)')
        db.commit()

@app.route('/')
@auth.login_required
def dashboard():
    db = get_db()
    latest = db.execute('SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 1').fetchone()
    data = db.execute('''
        SELECT strftime("%H:%M", timestamp) as time, 
               temperature, humidity, pressure, 
               light, air_quality 
        FROM sensor_data 
        ORDER BY timestamp DESC 
        LIMIT 24
    ''').fetchall()
    
    stats = db.execute('''
        SELECT AVG(temperature) as avg_temp,
               MAX(temperature) as max_temp,
               MIN(temperature) as min_temp,
               AVG(humidity) as avg_hum,
               AVG(pressure) as avg_pres,
               AVG(light) as avg_light
        FROM sensor_data
        WHERE timestamp >= datetime('now', '-1 day')
    ''').fetchone()
    
    return render_template('dashboard.html',
                         latest=latest,
                         data=data,
                         stats=stats)

@app.route('/api/datos', methods=['POST'])
@auth.login_required
def receive_data():
    data = request.get_json()
    
    required = ['device_id', 'temperature', 'humidity', 'pressure']
    if not all(field in data for field in required):
        return jsonify({'status': 'error', 'message': 'Faltan campos requeridos'}), 400
    
    db = get_db()
    db.execute('''
        INSERT INTO sensor_data (
            device_id, temperature, humidity, pressure,
            light, air_quality_raw, air_quality, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('device_id'),
        data.get('temperature'),
        data.get('humidity'),
        data.get('pressure'),
        data.get('light', 0),
        data.get('air_quality_raw', 0),
        data.get('air_quality', 'Desconocida'),
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))
    db.commit()
    
    return jsonify({'status': 'success', 'message': 'Datos recibidos'})

@app.route('/api/graficas')
@auth.login_required
def graficas_data():
    db = get_db()
    data = db.execute('''
        SELECT strftime("%H:%M", timestamp) as time, 
               temperature, humidity, pressure, light 
        FROM sensor_data 
        ORDER BY timestamp DESC 
        LIMIT 12
    ''').fetchall()
    
    return jsonify({
        'labels': [d['time'] for d in reversed(data)],
        'temperatura': [d['temperature'] for d in reversed(data)],
        'humedad': [d['humidity'] for d in reversed(data)],
        'presion': [d['pressure'] for d in reversed(data)],
        'luz': [d['light'] for d in reversed(data)]
    })

if __name__ == '__main__':
    if not os.path.exists(app.config['DATABASE']):
        init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
