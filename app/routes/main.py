from flask import Blueprint, jsonify, request, current_app
from app.models.user import LoginPayload
from pydantic import ValidationError
from app import db
from bson import ObjectId
from app.models.products import *
from app.models.sale import Sale
from app.decorators import token_required
from datetime import datetime, timedelta, timezone
import jwt
import csv
import os
import io

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
        {"$set": update_data.model_dump(exclude_unset=True)}
    )

    if update_result.matched_count == 0:
        return jsonify({'error':'Produto não encontrado.'}), 404
    
    updated_product = db.products.find_one({"_id": oid})
    updated_product = ProductDBModel(**updated_product).model_dump(by_alias=True, exclude_none=True)
    return jsonify(updated_product)

# RF: O sistema deve permitir a delecao de um unico produto e produto existente
@main_bp.route('/product/<string:product_id>', methods=['DELETE'])
@token_required
def delete_product(token, product_id):
    try:
        oid = ObjectId(product_id)
    except Exception:
        return jsonify({'error':'Id do produto inválido.'}), 400
    
    deleted_product = db.products.delete_one({"_id": oid})
    if deleted_product.deleted_count == 0:
        return jsonify({'error':'Produto não encontrado.'}), 404
    
    return "", 204

# RF: O sistema deve permitir a importacao de vendas através de um arquivo
@main_bp.route('/sales/upload', methods=['POST'])
@token_required
def upload_sales(token):
    if 'file' not in request.files:
        return jsonify({'error':'Nenhum arquivo foi enviado.'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error':'Nenhum arquivo selecionado.'}), 400
    
    if file and file.filename.endswith('.csv'):
        csv_stream = io.StringIO(file.stream.read().decode('UTF-8'), newline=None)
        csv_reader = csv.DictReader(csv_stream)

        sales_to_insert = []
        errors = []

        for row_num, row in enumerate(csv_reader, 1):
            try:
                sale_data = Sale(**row)
                sales_to_insert.append(sale_data.model_dump())
            except ValidationError as e:
                errors.append(f'Linha {row_num} com dados inválidos.')
            except Exception:
                errors.append(f'Linha {row_num} com erro inesperado nos dados.')

        if sales_to_insert:
            try:
                db.sales.insert_many(sales_to_insert)
            except Exception as e:
                return jsonify({'error':f'{e}'})
        return jsonify({
            "message": "Upload realizado com sucesso.",
            "vendas importadas": len(sales_to_insert),
            "erros encontrados": errors
        }), 200
    
    return jsonify({'error':'Formato de '})

@main_bp.route('/')
def index():
    return jsonify({'message':'Bem vindo ao StyleSync!'})



