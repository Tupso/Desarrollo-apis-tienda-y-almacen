import sqlite3
import os


def create_db(db_path):
    if not os.path.exists(db_path):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Conexión a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Creación de la tabla de productos si no existe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articulos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                cantidad INTEGER NOT NULL DEFAULT 15,
                disponible BOOLEAN NOT NULL DEFAULT TRUE
            )
        ''')
        conn.commit()
        conn.close()
    else:
        print(f"La base de datos ya existe en: {db_path}")

# Obtener los resultados
# cursor.execute("SELECT * FROM articulos")
# results = cursor.fetchall()
# print(results)


