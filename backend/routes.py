from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = 27017

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
@app.route("/song", methods=['GET'])
def list_song():
    _datas = list(db.songs.find())
    if not _datas:
        return {"message": "Not found data"}, 404
    return jsonify(parse_json(list(_datas))), 200

@app.route("/song", methods=['POST'])
def create_song():
    obj = request.json

    existing = db.songs.find_one({"id": obj.get("id")})
    if existing:
        return (
            jsonify({"Message": f"song with id {obj['id']} already present"}),
            302,
        )

    db.songs.insert_one(obj)
    return jsonify(obj), 201

@app.route("/song/<int:song_id>", methods=['GET'])
def read_song(song_id):
    _datas = db.songs.find()
    for it in _datas:
        if it['id'] == int(song_id):
            return jsonify(parse_json(it)), 200
    return {"message": "Not found data"}, 404

@app.route("/song/<int:song_id>", methods=['PUT'])
def update_song(song_id):
    obj = request.json

    # Kiểm tra song có tồn tại không
    existing = db.songs.find_one({"id": song_id})
    if not existing:
        return jsonify({"message": "song not found"}), 404

    # Nếu có thì update
    db.songs.update_one({"id": song_id}, {"$set": obj})
    return jsonify({"message": "updated"}), 200

@app.route("/song/<int:song_id>", methods=['DELETE'])
def delete_song(song_id):
    result = db.songs.delete_one({"id": int(song_id)})
    if result.deleted_count == 0:
        return jsonify({"message": "song not found"}), 404

    return "", 204

@app.route("/health")
def check_health():
    return {"status": "ok"}, 200

@app.route("/count")
def count_song():
    count = db.songs.count_documents({})
    return {"count": count}