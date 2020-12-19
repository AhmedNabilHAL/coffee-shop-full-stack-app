import os
import json
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

db_drop_and_create_all()

## ROUTES
@app.route("/drinks", methods=['GET'])
def get_drinks():
    drinks = Drink.query.all()
    if drinks is None or len(drinks) == 0:
        abort(404)

    drinks = [drink.short() for drink in drinks]
    return jsonify({
        "success": True,
        "drinks": drinks
    })

@app.route("/drinks-detail", methods=['GET'])
@requires_auth(permission="get:drinks-detail")
def get_drinks_details(payload):
    drinks = Drink.query.all()
    if drinks is None or len(drinks) == 0:
        abort(404)

    drinks = [drink.long() for drink in drinks]
    return jsonify({
        "success": True,
        "drinks": drinks
    })

@app.route("/drinks", methods=['POST'])
@requires_auth(permission="post:drinks")
def create_drink(payload):
    body = request.get_json()
    check_request(body)

    conflicts = Drink.query.filter(Drink.title==body["title"]).all()
    if len(conflicts) != 0:
        abort(409)
        
    drink = Drink(title=body["title"], recipe=json.dumps(body["recipe"]))
    drink.insert()
    return jsonify({
        "success": True,
        "drinks": [
            drink.long()
        ]
    })

@app.route("/drinks/<int:id>", methods=['PATCH'])
@requires_auth(permission='patch:drinks')
def update_drink(payload, id):
    body = request.get_json()
    check_request(body)

    drink = Drink.query.get(id)
    if drink is None:
        abort(404)

    drink.title = body["title"]
    drink.recipe = json.dumps(body["recipe"])
    drink.update()
    return jsonify({
        "success": True,
        "drinks": [
            drink.long()
        ]
    })    

@app.route("/drinks/<int:id>", methods=['DELETE'])
@requires_auth(permission='delete:drinks')
def delete_drink(payload, id):
    drink = Drink.query.get(id)
    if drink is None:
        abort(404)

    drink.delete()
    return jsonify({
        "success": True,
        "delete": id
    })

## Error Handling
'''
Example error handling for unprocessable entity
'''
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False, 
                    "error": 422,
                    "message": "unprocessable"
                    }), 422

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
                    "success": False, 
                    "error": 400,
                    "message": "bad request"
                    }), 400

@app.errorhandler(404)
def notFound(error):
    return jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

@app.errorhandler(409)
def conflict(error):
    return jsonify({
                    "success": False,
                    "error": 409,
                    "message": "title already exists"
                    }), 409                    

@app.errorhandler(AuthError)
def authErrorHandler(error):
    return jsonify({
                    "success": False, 
                    "error": error.status_code,
                    "message": error.error["description"]
                    }), error.status_code

# helper function to ensure correct request structure
def check_request(body):
    if body is None or "title" not in body or "recipe" not in body or not isinstance(body["recipe"], list):
        abort(400)
    else:
        for r in body["recipe"]:
            if "color" not in r or "name" not in r or "parts" not in r:
                abort(400)
    
    if not isinstance(body["title"], str) or not isinstance(body["recipe"], list):
        abort(422)
    else:
        for r in body["recipe"]:
            if not isinstance(r["color"], str) or not isinstance(r["name"], str) or not isinstance(r["parts"], int): 
                abort(422)

    if len(body["title"]) == 0:
        abort(400)
    else:
        for r in body["recipe"]:
            if len(r["color"]) == 0 or len(r["name"]) == 0:
                abort(400)                    