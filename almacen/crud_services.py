import sqlite3


def get_db_connection(db_path):
    return sqlite3.connect(db_path)


def get_articulos(db_path):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM articulos')
    articulos = cursor.fetchall()
    conn.close()
    return articulos


def get_articulo(db_path, id):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM articulos WHERE id=?', (id,))
    articulo = cursor.fetchone()
    conn.close()

    if articulo:
        return {
            'id': articulo[0],
            'nombre': articulo[1],
            'descripcion': articulo[2],
            'cantidad': articulo[3],
            'disponible': bool(articulo[4])
        }
    else:
        return None


def create_articulo(db_path, nombre, descripcion='', cantidad=0, disponible=True):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO articulos (nombre, descripcion, cantidad, disponible) VALUES (?, ?, ?, ?)', (nombre, descripcion, cantidad, disponible))
    conn.commit()
    conn.close()


def update_articulo(db_path, id, data):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Construir la sentencia SQL de actualización
    sql = 'UPDATE articulos SET '
    params = []
    for key, value in data.items():
        if key != 'id':  # Evitar actualizar el ID
            sql += f'{key}=?, '
            params.append(value)
    sql = sql.rstrip(', ')  # Eliminar la coma final
    sql += ' WHERE id=?'
    params.append(id)

    # Ejecutar la sentencia SQL de actualización
    cursor.execute(sql, params)
    conn.commit()
    conn.close()


def delete_articulo(db_path, id):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM articulos WHERE id = ?', (id,))
    conn.commit()
    conn.close()


def incrementar_articulo(db_path, id, cantidad):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('UPDATE articulos SET cantidad = cantidad + ? WHERE id = ?', (cantidad, id))
    conn.commit()
    updated_rows = cursor.rowcount
    conn.close()
    return updated_rows


def disminuir_articulo(db_path, id, cantidad):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('UPDATE articulos SET cantidad = cantidad - ? WHERE id = ?', (cantidad, id))
    conn.commit()
    updated_rows = cursor.rowcount
    conn.close()
    return updated_rows

