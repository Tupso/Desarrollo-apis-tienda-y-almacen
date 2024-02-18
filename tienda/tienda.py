import yaml
import argparse
from bd import create_db, traspasar_productos_almacen
from flask import Flask, jsonify, request, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
from crud_services import get_productos, get_producto, create_producto, update_producto, \
    delete_producto, solicitar_producto
import os


# Función para cargar la configuración desde un archivo YAML
def load_config(config_path):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


# Crear la aplicación Flask
app = Flask(__name__)


# Servicios CRUD para la administración de productos
@app.route('/productos', methods=['GET'])
def obtener_productos():
    productos = get_productos(config['basedatos']['path'])
    return jsonify({'productos': productos})


# GET request de todos los productos de la base de datos
@app.route('/productos/<int:id>', methods=['GET'])
def obtener_producto(id):
    producto = get_producto(config['basedatos']['path'], id)
    if producto:
        return jsonify({'producto': producto})
    else:
        return jsonify({'message': 'Producto no encontrado'}), 404


# GET request de un producto en concreto de la base de datos
@app.route('/productos', methods=['POST'])
def crear_producto():
    data = request.json
    nombre = data['nombre']
    descripcion = data.get('descripcion', '')
    cantidad = data.get('cantidad', 0)
    precio = data.get('precio', 0)
    nuevo_producto = create_producto(config['basedatos']['path'], nombre, descripcion, cantidad, precio)
    return jsonify({'message': 'Producto creado correctamente', 'producto': nuevo_producto}), 201


# PUT request para actualizar un producto en concreto de la base de datos
@app.route('/productos/<int:id>', methods=['PUT'])
def actualizar_producto(id):
    data = request.json
    update_producto(config['basedatos']['path'], id, data)
    return jsonify({'message': 'Producto actualizado correctamente'})


# PUT request para modificar específicamente el precio de un producto de la base de datos
@app.route('/productos/<int:id>/precio', methods=['PUT'])
def modificar_precio(id):
    data = request.json
    nuevo_precio = data.get('precio')

    if nuevo_precio is None:
        return jsonify({'message': 'Se requiere el nuevo precio'}), 400

    update_producto(config['basedatos']['path'], id, {'precio': nuevo_precio})
    return jsonify({'message': 'Precio del producto actualizado correctamente'})


# DELETE para eliminar un producto en concreto de la base de datos
@app.route('/productos/<int:id>', methods=['DELETE'])
def eliminar_producto(id):
    delete_producto(config['basedatos']['path'], id)
    return jsonify({'message': 'Producto eliminado correctamente'})


# Servicio para traer un producto, indicando ID y cantidad del almacén a la tienda
@app.route('/traspaso', methods=['POST'])
def traspaso():
    data = request.json
    producto_id = data.get('id')
    cantidad_solicitada = data.get('cantidad')

    config = load_config('config.yaml')
    result, status_code = solicitar_producto(producto_id, cantidad_solicitada, config, args.key)

    return jsonify(result), status_code


# Post request para vender una unidad de un producto
@app.route('/productos/<int:id>/venta', methods=['POST'])
def vender_producto(id):
    producto = get_producto(config['basedatos']['path'], id)

    if producto is None:
        return jsonify({'message': 'Producto no encontrado'}), 404

    cantidad_disponible = producto['cantidad']
    precio = producto['precio']

    if cantidad_disponible < 1:
        return jsonify({'message': 'No hay unidades disponibles para vender'}), 400

    # Verificar que tiene precio
    if precio is None:
        return jsonify({'message': 'No se ha establecido el precio del producto'}), 400

    # Decrementar las unidades disponibles e incrementar las unidades vendidas
    update_producto(config['basedatos']['path'], id,
                        {'cantidad': cantidad_disponible - 1, 'vendidas': producto['vendidas'] + 1})

    return jsonify({'message': 'Se ha vendido una unidad del producto correctamente'})


# Función para cargar la configuración y parsear los argumentos de línea de comandos
def configurar_aplicacion():
    parser = argparse.ArgumentParser(description='Aplicación Tienda')
    parser.add_argument('--servidor', type=str, default='localhost', help='IP o nombre del servidor donde se inicia la aplicación')
    parser.add_argument('--puerto', type=int, default=5001, help='Puerto donde se expondrá el API')
    parser.add_argument('--config', type=str, required=True, help='Ruta y nombre del fichero de configuración de la aplicación')
    parser.add_argument('--key', type=str, required=True, help='Valor del API KEY para consumir servicios de la aplicación almacen')
    args = parser.parse_args()
    return args


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
    # Parsear argumentos de línea de comandos
    args = configurar_aplicacion()

    # Cargar la configuración
    config = load_config(args.config)

    # Llama a la función para inicializar la base de datos de la tienda y traspasar productos
    #
    if not os.path.exists(config['basedatos']['path']):
        create_db(config['basedatos']['path'])
        traspasar_productos_almacen(config['basedatos']['path'], args.key)

    # Ejecuta la aplicación Flask
    app.run(host=args.servidor, port=args.puerto)
