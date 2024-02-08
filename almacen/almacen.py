import sqlite3
import argparse
import yaml
from flask import Flask, jsonify, request, send_from_directory
from flasgger import Swagger, swag_from
from flask_swagger_ui import get_swaggerui_blueprint
from functools import wraps
from bd import create_db

app = Flask(__name__)


def load_config(config_path):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


def get_db_connection(db_path):
    return sqlite3.connect(db_path)


def validar_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get('API-Key')

        if api_key != config['basedatos']['consumidor_almacen_key']:
            return jsonify({'message': 'API Key inválida'}), 401

        return func(*args, **kwargs)

    return wrapper


@app.route('/articulos', methods=['GET'])
def get_articulos():
    db_connection = get_db_connection(config['basedatos']['path'])
    cursor = db_connection.cursor()
    cursor.execute('SELECT * FROM articulos')
    articulos = cursor.fetchall()
    db_connection.close()
    return jsonify(articulos)


@app.route('/articulos/<int:id>', methods=['GET'])
def get_articulo(id):
    db_connection = get_db_connection(config['basedatos']['path'])
    cursor = db_connection.cursor()
    cursor.execute('SELECT * FROM articulos WHERE id = ?', (id,))
    articulo = cursor.fetchone()
    db_connection.close()
    return jsonify(articulo)


@app.route('/articulos', methods=['POST'])
def create_articulo():
    data = request.json
    nombre = data['nombre']
    descripcion = data.get('descripcion', '')
    cantidad = data.get('cantidad', 0)
    disponible = data.get('disponible', 0)

    db_connection = get_db_connection(config['basedatos']['path'])
    cursor = db_connection.cursor()
    cursor.execute('INSERT INTO articulos (nombre, descripcion, cantidad, disponible) VALUES (?, ?, ?, ?)',
                   (nombre, descripcion, cantidad, disponible))
    db_connection.commit()
    db_connection.close()
    return jsonify({'message': 'Artículo creado correctamente'}), 201


@app.route('/articulos/<int:id>', methods=['PUT'])
def update_articulo(id):
    data = request.json
    nombre = data['nombre']
    descripcion = data.get('descripcion', '')
    cantidad = data.get('cantidad', 0)
    disponible = data.get('disponible', 0)

    db_connection = get_db_connection(config['basedatos']['path'])
    cursor = db_connection.cursor()
    cursor.execute('UPDATE articulos SET nombre=?, descripcion=?, cantidad=?, disponible=? WHERE id=?',
                   (nombre, descripcion, cantidad, disponible, id))
    db_connection.commit()
    db_connection.close()
    return jsonify({'message': 'Artículo actualizado correctamente'})


@app.route('/articulos/<int:id>', methods=['DELETE'])
def delete_articulo(id):
    db_connection = get_db_connection(config['basedatos']['path'])
    cursor = db_connection.cursor()
    cursor.execute('DELETE FROM articulos WHERE id = ?', (id,))
    db_connection.commit()
    db_connection.close()
    return jsonify({'message': 'Artículo eliminado correctamente'})


@app.route('/articulos/<int:id>/incrementar', methods=['PUT'])
@validar_api_key
def incrementar_articulo(id):
    data = request.json
    cantidad = data.get('cantidad', 1)

    db_connection = get_db_connection(config['basedatos']['path'])
    cursor = db_connection.cursor()
    cursor.execute('UPDATE articulos SET cantidad = cantidad + ? WHERE id = ?', (cantidad, id))
    db_connection.commit()

    updated_rows = cursor.rowcount
    db_connection.close()

    if updated_rows == 0:
        return jsonify({'message': 'El artículo no existe'}), 404
    else:
        return jsonify({'message': 'Cantidad del artículo incrementada correctamente'})


@app.route('/articulos/<int:id>/disminuir', methods=['PUT'])
@validar_api_key
def disminuir_articulo(id):
    data = request.json
    cantidad = data.get('cantidad', 1)

    db_connection = get_db_connection(config['basedatos']['path'])
    cursor = db_connection.cursor()
    cursor.execute('UPDATE articulos SET cantidad = cantidad - ? WHERE id = ?', (cantidad, id))
    db_connection.commit()

    updated_rows = cursor.rowcount
    db_connection.close()

    if updated_rows == 0:
        return jsonify({'message': 'El artículo no existe'}), 404
    else:
        return jsonify({'message': 'Cantidad del artículo disminuida correctamente'})

    # Se crea la ruta y la funcion para acceder a la documentacion de la API


# Ruta para mostrar el archivo api_doc.yaml
SWAGGER_URL = '/api/docs'
API_URL = '/services/spec'

# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "Test API"
    }
)

app.register_blueprint(swaggerui_blueprint)


@app.route(API_URL)
def get_spec():
    return send_from_directory(".", "api_doc.yaml")


if __name__ == '__main__':
    # Parseamos los parámetros
    parser = argparse.ArgumentParser(description="Almacén App")
    parser.add_argument("--servidor", default="localhost", help="IP o nombre del servidor (por defecto: localhost)")
    parser.add_argument("--puerto", default=5000, type=int, help="Puerto donde se expondrá el API (por defecto: 5000)")
    parser.add_argument("--config", required=True, help="Ruta y nombre del fichero de configuración")
    args = parser.parse_args()

    config = load_config(args.config)
    create_db(config['basedatos']['path'])

