from fastapi import FastAPI, HTTPException, Body
from datetime import date
from pymongo import MongoClient
from pydantic import BaseModel
from dotenv import load_dotenv
import urllib
import os

load_dotenv(".env")

DATABASE_NAME = "hotel"
COLLECTION_NAME = "reservation"
USERNAME = os.getenv('username')
PASSWORD = os.getenv('password')
MONGO_DB_URL = "mongodb://localhost:27017"
MONGO_KU_SERVER_URL = f"mongodb://{USERNAME}:{PASSWORD}@mongo.exceed19.online:8443/?authMechanism=DEFAULT"
MONGO_DB_PORT = 8443


class Reservation(BaseModel):
    name: str
    start_date: date
    end_date: date
    room_id: int


client = MongoClient(MONGO_DB_URL)

db = client[DATABASE_NAME]

collection = db[COLLECTION_NAME]

app = FastAPI()


def room_avaliable(room_id: int, start_date: str, end_date: str):
    query = {"room_id": room_id,
           "$or": 
                [{"$and": [{"start_date": {"$lte": start_date}}, {"end_date": {"$gte": start_date}}]},
                 {"$and": [{"start_date": {"$lte": end_date}}, {"end_date": {"$gte": end_date}}]},
                 {"$and": [{"start_date": {"$gte": start_date}}, {"end_date": {"$lte": end_date}}]}]
            }
    
    result = collection.find(query, {"_id": 0})
    list_cursor = list(result)

    return not (len(list_cursor) > 0)


@app.get("/reservation/by-name/{name}")
def get_reservation_by_name(name: str):
    result = collection.find({"name": name}, {"_id": False})
    list_cursor = list(result)
    return {"result": list_cursor}


@app.get("/reservation/by-room/{room_id}")
def get_reservation_by_room(room_id: int):
    result = collection.find({"room_id": room_id}, {"_id": False})
    list_cursor = list(result)
    return {"result": list_cursor}


@app.post("/reservation", status_code=200)
def reserve(reservation: Reservation):
    if not (0 < reservation.room_id < 11):
        raise HTTPException(400)
    if not (reservation.start_date <= reservation.end_date):
        raise HTTPException(400)
    if not room_avaliable(reservation.room_id, str(reservation.start_date), str(reservation.end_date)):
        raise HTTPException(400)
    collection.insert_one({"name": reservation.name,
                           "start_date": reservation.start_date.strftime("%Y-%m-%d"),
                           "end_date": reservation.end_date.strftime("%Y-%m-%d"),
                           "room_id": reservation.room_id})


@app.put("/reservation/update")
def update_reservation(reservation: Reservation, new_start_date: date = Body(), new_end_date: date = Body()):
    if not (new_start_date <= new_end_date):
        raise HTTPException(400)
    if not room_avaliable(reservation.room_id, str(new_start_date), str(new_end_date)):
        raise HTTPException(400)
    collection.update_one({"name": reservation.name,
                           "start_date": reservation.start_date.strftime("%Y-%m-%d"),
                           "end_date": reservation.end_date.strftime("%Y-%m-%d"),
                           "room_id": reservation.room_id},
                          update={"$set": {"start_date": new_start_date.isoformat(),
                                           "end_date": new_end_date.isoformat()}})


@app.delete("/reservation/delete")
def cancel_reservation(reservation: Reservation):
    collection.delete_one({"name": reservation.name,
                           "start_date": reservation.start_date.strftime("%Y-%m-%d"),
                           "end_date": reservation.end_date.strftime("%Y-%m-%d"),
                           "room_id": reservation.room_id})
