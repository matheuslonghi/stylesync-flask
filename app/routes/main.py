from flask import Blueprint, jsonify, request, current_app
from app.models.user import LoginPayload
from pydantic import ValidationError
from app import db
from bson import ObjectId
from app.models.products import *
from app.decorators import token_required
from datetime import datetime, timedelta, timezone
import jwt

main_bp = Blueprint('main_bp', __name__)

# RF: O sistema deve permitir que um usuário se autentique para obter um token
@main_bp.route('/login', methods=['POST'])
def login():
    try:
        raw_data = request.get_json()
        user_data = LoginPayload(**raw_data)

    except ValidationError as e:
        return jsonify({'error':e.errors()}), 400
    except Exception:
        return jsonify({'error':'Corpo da requisição inválido ou não é um JSON.'})
    
    if user_data.username == 'admin' and user_data.password == 'supersecret':
        token = jwt.encode(
            {
                "user_id": user_data.username,
                "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
            },
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )

        return jsonify({'access_token':token}), 200

    return jsonify({'error':'Credenciais inválidas.'}), 401
    

# RF: O sistema deve permitir listagem de todos os produtos
@main_bp.route('/products', methods=['GET'])
def get_products():
    products_cursor = db.products.find({})
    products_list = [ProductDBModel(**product).model_dump(by_alias=True, exclude_none=True) for product in products_cursor]
    return jsonify(products_list)

# RF: O sistema deve permitir a criacao de um novo produto
@main_bp.route('/products', methods=['POST'])
@token_required
def create_product(token):
    try:
        product = Product(**request.get_json())
    except ValidationError as e:
        jsonify({'error':e.errors()})
    
    result = db.products.insert_one(product.model_dump(exclude_none=True))

    return jsonify({'message':'Esta é a rota de criação de produto!',
                    'id':str(result.inserted_id)}), 201

# RF: O sistema deve permitir a visualizacao dos detalhes de um unico produto
@main_bp.route('/product/<string:product_id>', methods=['GET'])
def get_product_by_id(product_id):
    try:
        oid = ObjectId(product_id)
    except Exception as e:
        return jsonify({'error':f'Erro ao transformar o {product_id} em ObjectID: {e}'})
    
    product = db.products.find_one({'_id':oid})

    if product:
        product_model = ProductDBModel(**product).model_dump(by_alias=True, exclude_none=True)
        return jsonify(product_model)
    else:
        return jsonify({'error':f'Produto com o ID: {product_id} - Não encontrado.'})

# RF: O sistema deve permitir a atualizacao de um unico produto e produto existente
@main_bp.route('/product/<string:product_id>', methods=['PUT'])
@token_required
def update_product(token, product_id):
    try:
        oid = ObjectId(product_id)
        update_data = UpdateProduct(**request.get_json())
    except ValidationError as e:
        return jsonify({'error':e.errors()})
    
    update_result = db.products.update_one(
        {"_id": oid},
        {"$set": update_data.model_dump}
    )

    if update_product

    return jsonify({'message':f'Esta é a rota de atualização do produto {product_id}!'})

# RF: O sistema deve permitir a delecao de um unico produto e produto existente
@main_bp.route('/product/<string:product_id>', methods=['DELETE'])
def delete_product(product_id):
    return jsonify({'message':f'Esta é a rota de deleção do produto {product_id}!'})

# RF: O sistema deve permitir a importacao de vendas através de um arquivo
@main_bp.route('/sales/upload', methods=['POST'])
def upload_sales():
    return jsonify({'message':'Esta é a rota do upload do arquivo de vendas!'})

@main_bp.route('/')
def index():
    return jsonify({'message':'Bem vindo ao StyleSync!'})



