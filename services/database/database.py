from pymongo import MongoClient
import functools
import json
from flask import Flask, jsonify, request, make_response
import copy, requests

client = MongoClient('mongo', 27017, username='root', password='root')

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


# GET:      curl "http://127.0.0.1:5002?collection=shoplist&database=organizer"
# POST:     curl --header "Content-Type: application/json" --request POST --data '{ "collection": "shoplist", "database": "organizer", "data": [{"name":"test4", "user": "zaqwer101"}]}' http://127.0.0.1:5002 -k
# DELETE:   curl --header "Content-Type: application/json" --request DELETE --data '{"collection": "shoplist", "database": "organizer", "data": [{"user": "zaqwer1011"}] }' "http://127.0.0.1:5002" -k
# PUT:      curl --header "Content-Type: application/json" --request PUT --data '{ "collection": "shoplist", "database": "organizer", "query": {"name": "test6"}, "data": {"name": "test228"} }' http://127.0.0.1:5002 -k
@app.route('/', methods=['GET', 'POST', 'DELETE', 'PUT'])
@check_params(params_get=['database', 'collection'],
              params_post=['database', 'collection', 'data'],
              params_delete=['database', 'collection', 'data'],
              params_put=['database', 'collection',
                          'query',  # условие, какие элементы меняем
                          'data'])  # на что меняем
def database_handler():
    # получаем данные из БД
    # query=get
    if request.method == 'GET':
        service_params = ['database', 'collection']
        db_name = request.args['database']
        collection_name = request.args['collection']
        query = {}
        result = []

        for arg in request.args.keys():
            if arg not in service_params:
                query[arg] = request.args[arg]
                
        app.logger.info(f'GET query: {query}')
        db = client[db_name]
        collection = db[collection_name]

        for elem in collection.find(query):
            elem['id'] = str(elem['_id'])
            del elem['_id']
            app.logger.info(f'  Elem: {elem}')
            result.append(elem)
        if len(result) == 0:
            return error("not found", 404)
        return jsonify(result)  # статус 200 по умолчанию


    # вносим данные в БД
    elif request.method == 'POST':
        db_name = request.get_json()['database']
        collection_name = request.get_json()['collection']
        db = client[db_name]
        collection = db[collection_name]
        data = request.get_json()['data']
        app.logger.info(f'POST data: {data}')

        if len(data) != 0:
            out = []
            for elem in request.get_json()['data']:
                app.logger.info(f'   Elem: {elem}')
                out.append(str(collection.insert_one(elem).inserted_id))
            return make_response(jsonify({"output": out}), 201)  # объект создан
        else:
            return error("empty data", 400)


    elif request.method == 'DELETE':
        db_name = request.get_json()['database']
        collection_name = request.get_json()['collection']
        db = client[db_name]
        collection = db[collection_name]
        data = request.get_json()['data']
        app.logger.info(f'DELETE data: {data}')

        if len(data) != 0:
            for elem in request.get_json()['data']:
                count = collection.delete_many(elem).deleted_count
            return make_response(jsonify({"status": "success", "deleted": count}), 201)
        else:
            return error("empty data", 400)


    elif request.method == 'PUT':
        db_name = request.get_json()['database']
        collection_name = request.get_json()['collection']
        db = client[db_name]
        collection = db[collection_name]
        app.logger.info(f'PUT query: {request.get_json()["query"]}')
        app.logger.info(f'PUT data: {request.get_json()["data"]}')

        result = collection.update_one(
            request.get_json()['query'],
            {"$set": request.get_json()['data']}
        )

        if result.modified_count > 0:
            return jsonify({"status": "success"})
        else:
            return error("not found", 404)
