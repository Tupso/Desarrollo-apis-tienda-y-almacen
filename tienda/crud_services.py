import sqlite3
import requests
import yaml

# Cargamos la configuración
def cargar_configuracion(config_path):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


config = cargar_configuracion('config.yaml')


def get_db_connection(db_path):
    return sqlite3.connect(db_path)


def get_productos(db_path):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM productos')
    productos = cursor.fetchall()
    conn.close()
    if productos:
        return [{'id': producto[0], 'nombre': producto[1], 'descripcion': producto[2], 'cantidad': producto[3],
                'precio': producto[4], 'vendidas': producto[5]}for producto in productos]
    else:
        return None


def get_producto(db_path, id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM productos WHERE id=?', (id,))
    producto = cursor.fetchone()
    conn.close()
    if producto:
        return {'id': producto[0], 'nombre': producto[1], 'descripcion': producto[2], 'cantidad': producto[3],
                'precio': producto[4], 'vendidas': producto[5]}
    else:
        return None


def create_producto(db_path, nombre, descripcion, cantidad, precio):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO productos (nombre, descripcion, cantidad, precio) VALUES (?, ?, ?, ?)',
                   (nombre, descripcion, cantidad, precio))
    conn.commit()
    producto_id = cursor.lastrowid
    conn.close()
    return producto_id


def update_producto(db_path, producto_id, campos):
    # Construimos la consulta SQL dinámicamente
    query = 'UPDATE productos SET '
    values = []
    for key, value in campos.items():
        query += f"{key}=?, "
        values.append(value)
    query = query.rstrip(', ')  # Eliminamos la última coma
    query += ' WHERE id=?'
    values.append(producto_id)

    # Ejecutamos la consulta
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(query, values)
    conn.commit()
    conn.close()


def solicitar_producto(producto_id, cantidad_solicitada, config, args):
    # Consultar la disponibilidad de productos en el almacén
    url_almacen = f"http://{config['almacen']['servidor']}:{config['almacen']['puerto']}{config['almacen']['ruta_articulos']}?id={producto_id}"
    headers = {'API-Key': str(args)}

    try:
        response = requests.get(url_almacen, headers=headers)
        response.raise_for_status()
        producto_almacen = response.json().get('articulos', [])
    except requests.exceptions.RequestException as e:
        return {'message': f'Error al obtener el producto del almacén: {e}'}, 500

    articulos_almacen = producto_almacen
    if not articulos_almacen:
        return {'message': 'El producto no está disponible en el almacén'}, 404

    cantidad_disponible = articulos_almacen[0].get('cantidad', 0)

    if cantidad_disponible < cantidad_solicitada:
        return {'message': 'No hay suficientes unidades disponibles en el almacén'}, 400

    # Conectar a la base de datos de la tienda y actualizar la cantidad del producto
    try:
        conn_tienda = sqlite3.connect(config['basedatos']['path'])
        cursor_tienda = conn_tienda.cursor()
        cursor_tienda.execute("UPDATE productos SET cantidad = cantidad + ? WHERE id = ?",
                              (cantidad_solicitada, producto_id))
        conn_tienda.commit()
        print(f"Cantidad del producto {producto_id} actualizada en la tienda")
        conn_tienda.close()
    except Exception as e:
        return {'message': f'Error al actualizar la cantidad del producto en la tienda: {e}'}, 500

    # Actualizar la cantidad disponible del producto en el almacén
    nueva_cantidad_almacen = cantidad_disponible - cantidad_solicitada
    try:
        conn_almacen = sqlite3.connect('../almacen/db/almacen.db')
        cursor_almacen = conn_almacen.cursor()
        cursor_almacen.execute("UPDATE articulos SET cantidad = ? WHERE id = ?",
                              (nueva_cantidad_almacen, producto_id))
        conn_almacen.commit()
        print(f"Actualización de la cantidad del producto {producto_id} en el almacén realizada correctamente")
        conn_almacen.close()
    except Exception as e:
        return {'message': f'Error al actualizar la cantidad del producto en el almacén: {e}'}, 500

    return {'message': f'Producto {producto_id} traspasado almacén correctamente'}, 200


def delete_producto(db_path, producto_id):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM productos WHERE id=?', (producto_id,))
    conn.commit()
    conn.close()
