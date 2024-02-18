import argparse
import yaml
import sqlite3
from flask import Flask, jsonify, request, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
from functools import wraps
from bd import create_db
from crud_services import (get_articulos, get_articulo, create_articulo, update_articulo, delete_articulo,
                           incrementar_articulo, disminuir_articulo)

app = Flask(__name__)


def load_config(config_path):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


# Parseamos los parámetros
parser = argparse.ArgumentParser(description="Almacén App")
parser.add_argument("--servidor", default="localhost", help="IP o nombre del servidor (por defecto: localhost)")
parser.add_argument("--puerto", default=5000, type=int, help="Puerto donde se expondrá el API (por defecto: 5000)")
parser.add_argument("--config", required=True, help="Ruta y nombre del fichero de configuración")
args = parser.parse_args()

config = load_config(args.config)
create_db(config['basedatos']['path'])


def validar_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get("API-Key")

        if api_key != str(config['basedatos']['consumidor_almacen_api']):
            return jsonify({'message': 'API Key invalida'}), 401

        return func(*args, **kwargs)

    return wrapper


@app.route('/articulos', methods=['GET'])
@validar_api_key
def obtener_articulos():
    articulos = get_articulos(config['basedatos']['path'])
    articulos_json = [{'id': articulo[0], 'nombre': articulo[1], 'descripcion': articulo[2],
                       'cantidad': articulo[3], 'disponible': bool(articulo[4])}for articulo in articulos]
    return jsonify({'articulos': articulos_json})


@app.route('/articulos/<int:id>', methods=['GET'])
@validar_api_key
def obtener_articulo(id):
    articulo = get_articulo(config['basedatos']['path'], id)
    if articulo:
        return jsonify(articulo)
    else:
        return jsonify({'message': 'Artículo no encontrado'}), 404


@app.route('/articulos', methods=['POST'])
@validar_api_key
def crear_articulo():
    data = request.json
    nombre = data['nombre']
    descripcion = data.get('descripcion', '')
    cantidad = data.get('cantidad', 0)
    disponible = data.get('disponible', 0)

    create_articulo(config['basedatos']['path'], nombre, descripcion, cantidad, disponible)
    return jsonify({'message': 'Artículo creado correctamente'}), 201


@app.route('/articulos/<int:id>', methods=['PUT'])
@validar_api_key
def actualizar_articulo(id):
    data = request.json

    update_articulo(config['basedatos']['path'], id, data)
    return jsonify({'message': 'Artículo actualizado correctamente'})


@app.route('/articulos/<int:id>', methods=['DELETE'])
@validar_api_key
def eliminar_articulo(id):
    delete_articulo(config['basedatos']['path'], id)
    return jsonify({'message': 'Artículo eliminado correctamente'})


@app.route('/articulos/<int:id>/incrementar', methods=['PUT'])
@validar_api_key
def incrementar_cantidad_articulo(id):
    data = request.json
    cantidad = data.get('cantidad', 1)

    updated_rows = incrementar_articulo(config['basedatos']['path'], id, cantidad)

    if updated_rows == 0:
        return jsonify({'message': 'El artículo no existe'}), 404
    else:
        return jsonify({'message': 'Cantidad del artículo incrementada correctamente'})


@app.route('/articulos/<int:id>/disminuir', methods=['PUT'])
@validar_api_key
def disminuir_cantidad_articulo(id):
    data = request.json
    cantidad = data.get('cantidad', 1)

    updated_rows = disminuir_articulo(config['basedatos']['path'], id, cantidad)

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
    app.run(host=args.servidor,port=args.puerto)
