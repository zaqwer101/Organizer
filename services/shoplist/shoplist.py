import functools
from flask import Flask, jsonify, request, make_response
import requests, json

database = 'organizer'
collection = 'shoplist'
database_url = 'http://database:5000'
default_database_params = {"database": database, "collection": collection}
json_headers = {'content-type': 'application/json'}

app = Flask(__name__)
app.debug = True


def error(message, code):
    return make_response(jsonify({"error": message}), code)


def check_params(params_get=None, params_post=None, params_delete=None, params_put=None):
    def __check_params(func):
        @functools.wraps(func)
        def check_params_inner(*args, **kwargs):
            if request.method == 'GET':
                for param in params_get:
                    if not param in request.args:
                        return error("incorrect GET input", 400)
            if request.method == 'POST':
                for param in params_post:
                    if not param in request.get_json().keys():
                        return error("incorrect POST input", 400)
            if request.method == 'DELETE':
                for param in params_delete:
                    if not param in request.get_json().keys():
                        return error("incorrect DELETE input", 400)
            if request.method == 'PUT':
                for param in params_put:
                    if not param in request.get_json().keys():
                        return error("incorrect PUT input", 400)
            return func(*args, **kwargs)

        return check_params_inner

    return __check_params


@app.route('/', methods=['GET', 'POST', 'DELETE'])
@check_params(params_get=['user'],
              params_post=['user', 'name', 'shop'],
              params_delete=['user', 'name', 'shop'])
def shoplist():
    if request.method == 'GET':
        user = request.args['user']
        app.logger.info(f"GET / params: {request.args}")
        return get_items_by_user(user)

    if request.method == 'POST':
        user = request.get_json()['user']
        name = request.get_json()['name']
        shop = request.get_json()['shop']

        amount = 1
        if 'amount' in request.get_json():
            amount = request.get_json()['amount']
        app.logger.info(f"POST / params: " + str(request.get_json()))
        r = add_item(user, name, amount, shop)
        return r.json()

    if request.method == 'DELETE':
        user = request.get_json()['user']
        name = request.get_json()['name']
        shop = request.get_json()['shop']
        app.logger.info("DELETE / params: " + str(request.get_json()))
        r = database_request({"name": name, "user": user, "shop": shop}, 'DELETE')
        return r.json()


@app.route('/bought', methods=['POST'])
def set_bought():
    user = request.json['user']
    name = request.json['name']
    bought = request.json['bought']
    shop = request.json['shop']
    app.logger.info(user + ' ' + name + ' ' + bought + ' ' + shop)

    if change_bought(user, name, bought):
        return jsonify({"status": "success"})
    else:
        return error("item not found", 404)


def add_item(user, name, amount, shop):
    item = get_item_by_name(user, name)
    if item:  # значит элемент с таким именем уже есть в бд
        if item['shop'] == shop:  # проверяем, совпадают ли магазины элементов
            # если да - увеличиваем amount существующего
            data = {}
            data['query'] = {"user": user, "name": name}
            data['data'] = {"amount": item["amount"] + amount}
            r = database_request(data, 'PUT')
        else:  # если нет - добавляем как новый
            r = database_request({"user": user, "name": name, "amount": amount, "bought": "false", "shop": shop},
                                 'POST')
    else:  # значит нужно добавить новый элемент
        r = database_request({"user": user, "name": name, "amount": amount, "bought": "false", "shop": shop}, 'POST')
    return r


def change_bought(user, name, bought):
    item = get_item_by_name(user, name)
    if item:
        if item['bought'] == bought:
            return True
        data = {}
        data['query'] = {"user": user, "name": name}
        data['data'] = {"bought": bought}
        r = database_request(data, 'PUT')
        return True
    else:
        return False


def get_item_by_name(user, name):
    """ Найти все элементы пользователя с таким именем """
    r = database_request({"user": user, "name": name}, 'GET')
    if r.status_code == 400:
        error("incorrect params", 400)
    if r.status_code == 404:
        return None
    item = r.json()[0]
    return item


def get_items_by_user(user):
    """ Получить список всех элементов пользователя """
    r = database_request({"user": user}, 'GET')
    app.logger.info(r.json())
    app.logger.info(r.status_code)
    if r.status_code == 404:
        return jsonify([])
    if r.status_code == 400:
        return error("incorrect params", 400)
    return jsonify(r.json())


def database_request(params, request_method):
    """ Сделать запрос к сервису БД """
    app.logger.info(params)
    if request_method == 'POST':
        data = [params]
        query = {"database": database, "collection": collection, "data": data}
        app.logger.info(query)
        r = requests.post(database_url, json=query, headers=json_headers)

    if request_method == 'GET':
        if not 'database' in params:
            params['database'] = database
        if not 'collection' in params:
            params['collection'] = collection
        r = requests.get(database_url, params=params, headers=json_headers)

    if request_method == 'PUT':
        if not 'query' in params or not 'data' in params:
            app.logger.error("data or query param for PUT request is empty")
            return None
        r = requests.put(database_url, json={"database": database,
                                             "collection": collection,
                                             "query": params['query'],
                                             "data": params['data']})

    if request_method == 'DELETE':
        data = [params]
        r = requests.delete(database_url, json={"database": database,
                                                "collection": collection,
                                                "data": data})
    return r
