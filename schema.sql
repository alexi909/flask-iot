
        CREATE TABLE IF NOT EXISTS sensores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            temperatura REAL NOT NULL,
            humedad REAL NOT NULL,
            presion REAL NOT NULL,
            calidad_aire TEXT NOT NULL,
            luz REAL NOT NULL,
            fecha_hora DATETIME NOT NULL
        );
        
        CREATE INDEX IF NOT EXISTS idx_fecha ON sensores (fecha_hora);
    