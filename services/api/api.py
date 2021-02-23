import functools

from flask import Flask, jsonify, request, make_response
import requests
import json


app = Flask(__name__)
auth_url = "http://auth:5000"
shoplist_url = "http://shoplist:5000"
json_headers = {'content-type': 'application/json'}


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


def auth_needed(func):
    @functools.wraps(func)
    def check_auth(*args, **kwargs):
        if request.method == 'GET':
            app.logger.info('Wrapper GET request')
            if 'token' in request.args:
                token = request.args['token']
                user = check_auth_token(token)
                if user is None:
                    return error('invalid token', 400)
            else:
                return error('token not set', 400)

        elif request.method == 'POST':
            app.logger.info("Wrapper POST request")
            if 'token' in request.get_json():
                token = request.get_json()['token']
                user = check_auth_token(token)
                if user is None:
                    return error('invalid token', 400)
            else:
                return error('token not set', 400)
        return func(*args, **kwargs)

    return check_auth


def check_auth_token(token):
    """ Проверить токен, возвращает имя пользователя или None """
    r = requests.get(auth_url, params={"token": token})
    if 'user' in r.json():
        return r.json()['user']
    else:
        return None


def get_token(params):
    """ Получить токен авторизации по имени пользователя и паролю """
    r = requests.post(auth_url, json=params)
    if r.status_code == 200:
        return r.json()['token']
    else:
        return None


# POST: curl --header "Content-Type: application/json" --request POST --data '{ "user": "zaqwer101", "password": "1234"}' https://127.0.0.1/auth -k
@app.route('/auth', methods=['GET', 'POST'])
@check_params(params_get=['token'],
              params_post=['user'])
def auth():
    # проверяем токен авторизации
    if request.method == 'GET':
        token = request.args['token']
        user = check_auth_token(token)
        if user:
            return jsonify({"user": user})
        else:
            return error("invalid token", 401)

    # проверяем учетные данные и выдаём токен
    if request.method == 'POST':
        user = request.get_json()['user']
        params = {"user": user}
        if 'password_encrypted' in request.get_json():
            params['password_encrypted'] = request.get_json()['password_encrypted']
        elif 'password' in request.get_json():
            params['password'] = request.get_json()['password']
        else:
            error("no password provided", 400)
        token = get_token(params)
        if token is None:
            return error("invalid credentials", 401)
        return jsonify({"token": token})


@app.route('/info', methods=['GET'])
def get_services_metadata():
    """ Получить информацию о настройках сервисов """
    auth_info = requests.get(auth_url + '/info') # пока только auth

    metadata = {"auth": auth_info.json()}
    return jsonify(metadata)

@app.route('/shoplist', methods=['GET'])
@auth_needed
def shoplist_get_items():
    token = request.args['token']
    user = check_auth_token(token)

    r = requests.get(shoplist_url, params={"user": user})
    if r.status_code == 200:
        return jsonify(r.json())
    return error("incorrect input", 400)


@app.route('/shoplist', methods=['POST'])
@auth_needed
@check_params(params_post=['name'])
def shoplist_add_item():
    token = request.get_json()['token']
    user = check_auth_token(token)
    name = request.get_json()['name']

    if 'shop' in request.get_json():
        shop = request.get_json()['shop']
    else:
        shop = None

    params = {"user": user, "name": name, "bought": "false", "shop": shop}

    if 'amount' in request.get_json():
        params['amount'] = request.get_json()['amount']
    
    r = requests.post(shoplist_url, json=params)
    if r.status_code == 200:
        return make_response(jsonify({"status": "success"}), 201)
    else:
        return r.json()


@app.route('/shoplist/bought', methods=['POST'])
@auth_needed
@check_params(params_post=['name', 'bought'])
def bought():
    token = request.get_json()['token']
    user = check_auth_token(token)
    name = request.get_json()['name']
    bought = request.get_json()['bought']
    if 'shop' in request.get_json():
        shop = request.get_json().keys()['shop']
    else:
        shop = 'null'
    r = requests.post(f'{shoplist_url}/bought',
                      json={"user": user, "name": name, "bought": bought, "shop": shop})
    return r.json()


@app.route('/shoplist', methods=['DELETE'])
@auth_needed
@check_params(params_delete=['name'])
def shoplist_delete_item():
    token = request.get_json()['token']
    user = check_auth_token(token)
    name = request.get_json()['name']
    r = requests.delete(shoplist_url, json={'user': user, 'name': name})
    if r.status_code == 200:
        return jsonify({"status": "success"})
    return r.json()


@app.route('/register', methods=['POST'])
@check_params(params_post=['user', 'password'])
def register():
    user = request.get_json()['user']
    password = request.get_json()['password']
    r = requests.post(url=auth_url + '/register',
                      json={"user": user, "password": password})
    if r.status_code != 201: # если юзер в итоге не создался, ошибка
        return error(r.json()["error"], 400) 
    else:
        return r.json()
