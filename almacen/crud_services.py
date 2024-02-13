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
    cursor.execute('SELECT * FROM articulos WHERE id = ?', (id,))
    articulo = cursor.fetchone()
    conn.close()
    return articulo


def create_articulo(db_path, nombre, descripcion='', cantidad=0, disponible=0):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO articulos (nombre, descripcion, cantidad, disponible) VALUES (?, ?, ?, ?)', (nombre, descripcion, cantidad, disponible))
    conn.commit()
    conn.close()


def update_articulo(db_path, id, nombre, descripcion='', cantidad=0, disponible=0):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('UPDATE articulos SET nombre=?, descripcion=?, cantidad=?, disponible=? WHERE id=?', (nombre, descripcion, cantidad, disponible, id))
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

