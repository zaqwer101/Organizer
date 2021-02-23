from flask import Flask, jsonify, request, make_response
import hashlib
import string
import random
import requests
import redis as __redis


def error(message, code):
    return make_response(jsonify({"error": message}), code)


token_ttl = 86400
app = Flask(__name__)
redis = __redis.Redis(host='redis', port=6379, db=0)
database_url = 'http://database:5000'


@app.route('/register', methods=['POST'])
def register():
    user = request.get_json()['user']
    password = request.get_json()['password']
    password = encode_password(password)

    data = {
        "database": "organizer", "collection": "users",
        "data": [{
            "user": user, 
            "password": password
            }]
    }

    # если в БД уже есть такой юзер
    if get_user_by_name(user):
        return error("user exists", 400)

    # вносим юзера в БД
    r = requests.post(database_url + '/', json=data)

    if r.status_code == 201:
        return jsonify({"token": generate_token(user)}), 201
    elif r.status_code == 400:
        return error("something went wrong", 400)


@app.route('/', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        # войти с именем юзера и паролем
        user = request.get_json()['user']
        if 'password_encrypted' in request.get_json():
            # значит пароль уже пришел зашифрованным
            password = request.get_json()['password_encrypted']
        else:
            # иначе нужно зашифровать
            password = encode_password(request.get_json()['password'])
            
        if is_password_match(user, password):
            token = generate_token(user)
            app.logger.info(f'token: {token}')
            if not token:
                return error("max tokens exceeded", 400)
            return jsonify({"token": token})
        return error("invalid credentials", 401)

    if request.method == 'GET':
        # проверяем валидность токена
        if not 'token' in request.args:
            return error("no token provided", 400)
        token = request.args['token']

        user = get_user_by_token(token)
        if user:
            return jsonify({"user": user})
        else:
            return error("invalid token", 401)

@app.route('/info', methods=['GET'])
def get_service_info():
    return jsonify({"token_ttl": token_ttl})

def generate_token(user):
    letters = string.ascii_letters
    token = ''.join(random.choice(letters) for i in range(50))
    redis.set(token, user)
    redis.expire(token, token_ttl)
    return token


def get_user_by_name(user):
    r = requests.get(database_url, 
        params = {
            "database":     "organizer",
            "collection":   "users",
            "user":         user
            })

    if r.status_code == 200:
        return r.json()[0]
    else:
        return None


def is_password_match(user, password_encoded):
    user = get_user_by_name(user)
    app.logger.info(f'{user["user"]}: {user["password"]}')
    if user:
        if user['password'] == password_encoded:
            return True
    return False


def encode_password(password):
    return hashlib.md5(password.encode()).hexdigest()


def get_user_by_token(token):
    user = redis.get(token)
    if user:
        redis.expire(token, token_ttl)
        user = user.decode()
        return user
    else:
        return None
