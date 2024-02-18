import os
import sqlite3
import requests
import yaml


# Cargamos la configuración
def cargar_configuracion(config_path):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


config = cargar_configuracion('config.yaml')


def create_db(db_path):
    # Si la base de datos no existe, la crea
    if not os.path.exists(db_path):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Crea la tabla de productos si no existe
        cursor.execute('''CREATE TABLE IF NOT EXISTS productos (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            nombre TEXT NOT NULL,
                            descripcion TEXT,
                            cantidad INTEGER DEFAULT 0,
                            precio DOUBLE DEFAULT 0,
                            vendidas REAL DEFAULT 0
                        )''')
        conn.commit()
        conn.close()


# Función para traspasar 2 productos de la base de datos del almacén

def traspasar_productos_almacen(db_path, args):
    config = cargar_configuracion('config.yaml')

    # Consultar productos disponibles en el almacén
    url_almacen = f"http://{config['almacen']['servidor']}:{config['almacen']['puerto']}{config['almacen']['ruta_articulos']}"
    headers = {'API-Key': str(args)}

    try:
        response = requests.get(url_almacen, headers=headers)
        response.raise_for_status()
        productos_almacen = response.json().get('articulos', [])
    except requests.exceptions.RequestException as e:
        print(f'Error al obtener los productos del almacén: {e}')
        return

    # Conectar a la base de datos del almacén
    conn_almacen = sqlite3.connect('../almacen/db/almacen.db')
    cursor_almacen = conn_almacen.cursor()

    # Conectar a la base de datos de la tienda
    conn_tienda = sqlite3.connect(db_path)
    cursor_tienda = conn_tienda.cursor()

    # Insertar productos del almacén en la base de datos de la tienda
    for producto in productos_almacen:
        cantidad_traspasada = min(producto['cantidad'], 2)  # Traspasar un máximo de dos unidades
        cursor_tienda.execute("INSERT INTO productos (id, nombre, descripcion, cantidad) VALUES (?, ?, ?, ?)",
                              (producto['id'], producto['nombre'], producto['descripcion'], cantidad_traspasada))
        conn_tienda.commit()
        print(f"Producto {producto['id']} insertado en la tienda correctamente con cantidad {cantidad_traspasada}.")

        # Disminuir la cantidad de productos en la base de datos del almacén
        cursor_almacen.execute("UPDATE articulos SET cantidad = cantidad - ? WHERE id = ?", (cantidad_traspasada, producto['id']))
        conn_almacen.commit()
        print(f"Cantidad de producto {producto['id']} disminuida en el almacén.")

    conn_almacen.close()
    conn_tienda.close()
