import datetime   # This will be needed later
import os
from fastapi import FastAPI, Body, HTTPException, status
from dotenv import load_dotenv
from pymongo import MongoClient, ReturnDocument

 
from typing import Optional, List

from fastapi.responses import Response
from pydantic import ConfigDict, BaseModel, Field, EmailStr, ValidationError
from pydantic.functional_validators import BeforeValidator

from typing_extensions import Annotated

from bson import ObjectId
import motor.motor_asyncio

app = FastAPI(
    title = "Assignment",
    summary= "An assignment: to Create, Read, Update, and Delete Car information and Create, Read, Update, and Delete Broker information"
)


# Load config from a .env file:
load_dotenv()

client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGODB_URL"])

#connect to database "Company"
db = client.Company

#get collection "Car"
car_collection = db.get_collection("Car")

#get collection "Broker"
broker_collection = db.get_collection("Broker")


# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
PyObjectId = Annotated[str, BeforeValidator(str)]


class CarModel(BaseModel):
    """
        Model for a car record.
        Car is a product that we want to sales in our e-commerce website.
    """
    id: PyObjectId = Field(alias="_id", default=None)
    brand: str = Field(...)
    model: str = Field(...)
    year: str = Field(...)
    color: str = Field(...)
    mileage: float = Field(...)
    status: str = Field(...)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "brand": "Toyota",
                "model":"Yaris",
                "year":"2020",
                "color":"white",
                "mileage": 132000.0,
                "status":"active"
            }
        },
    )
    
class UpdateCarModel(BaseModel):
    """
        Model for a car record.
        Car is a product that we want to sales in our e-commerce website.
    """
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[str] = None
    color: Optional[str] = None
    mileage: Optional[float] = None
    status: Optional[str] = None
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "brand": "Toyota",
                "model":"Yaris",
                "year":"2020",
                "color":"white",
                "mileage": 132000.0,
                "status":"active"
            }
        },
    )
    
class CarCollection(BaseModel):
    cars: List[CarModel]
    

class BrokerModel(BaseModel):
    """
        Model for a broker record.
        Broker is a person that responsible for selling cars and a contact point if clients has any questions.
    """
    id: PyObjectId = Field(alias="_id", default=None)
    name: str = Field(...)
    branches: List[str] = Field(...)
    mobile_phone: str = Field(alias="mobile phone")
    email: EmailStr = Field(...)
    remark: str = Field(...)
    status: str = Field(...)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "name":"Jane doe",
                "branches":["Bangkok","Chonburi"],
                "mobile phone":"+66987654321",
                "email":"jane.doe@test.com",
                "remark":"telegram: +66987654321",
                "status":"active"
            }
        },
    )
    
class UpdateBrokerModel(BaseModel):
    """
        Model for a broker record.
        Broker is a person that responsible for selling cars and a contact point if clients has any questions.
    """
    name: Optional[str] = None
    branches: Optional[List] = None
    mobile_phone: Optional[str] = None
    email: Optional[EmailStr] = None
    remark: Optional[str] = None
    status: Optional[str] = None
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "name":"Jane doe",
                "branches":["Bangkok","Chonburi"],
                "mobile phone":"+66987654321",
                "email":"jane.doe@test.com",
                "remark":"telegram: +66987654321",
                "status":"active"
            }
        },
    )

class BrokerCollection(BaseModel):
    brokers: List[BrokerModel]


 
#API for Car

#List Car's id
@app.get(
    "/cars/ids",
    response_description="List all car IDs",
)
async def list_car_ids():
    """
    List all car IDs in the database.
    """
    # Retrieve all car records from the database
    cars = await car_collection.find().to_list(1000)

    # Extract IDs from car records
    car_ids = [str(car["_id"]) for car in cars]

    return car_ids

#create new car
@app.post(
    "/cars/",
    response_description="Add new car",
    response_model=CarModel,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
async def create_car(car: CarModel = Body(...)):
    """
    Insert a new car record.

    A unique `id` will be created and provided in the response.
    """
    new_car = await car_collection.insert_one(
        car.model_dump(by_alias=True, exclude=["id"])
    )
    created_car = await car_collection.find_one(
        {"_id": new_car.inserted_id}
    )
    return created_car

#list all car information
@app.get(
    "/cars/",
    response_description="List all cars",
    response_model=CarCollection,
    response_model_by_alias=False,
)
async def list_cars():
    """
    List all of the car data in the database.

    The response is unpaginated and limited to 1000 results.
    """
    
    return CarCollection(cars=await car_collection.find().to_list(1000))

#Show car by id
@app.get(
    "/cars/{id}",
    response_description="Get a single car",
    response_model=CarModel,
    response_model_by_alias=False,
)
async def show_car(id: str):
    """
    Get the record for a specific car, looked up by `id`.
    """
    
    if (car := await car_collection.find_one({"_id": ObjectId(id)})) is not None:
        return car

    raise HTTPException(status_code=404, detail=f"Car {id} not found")

#update car by id
@app.put(
    "/cars/{id}",
    response_description="Update a car",
    response_model=CarModel,
    response_model_by_alias=False,
)
async def update_car(id: str, car: UpdateCarModel = Body(...)):
    """
    Update individual fields of an existing car record.

    Only the provided fields will be updated.
    Any missing or `null` fields will be ignored.
    """
    car = {
        k: v for k, v in car.model_dump(by_alias=True).items() if v is not None
    }

    if len(car) >= 1:
        update_result = await car_collection.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": car},
            return_document=ReturnDocument.AFTER,
        )
        if update_result is not None:
            return update_result
        else:
            raise HTTPException(status_code=404, detail=f"car {id} not found")

    # The update is empty, but we should still return the matching document:
    if (existing_car := await car_collection.find_one({"_id": id})) is not None:
        return existing_car

    raise HTTPException(status_code=404, detail=f"car {id} not found")

#delete car by id
@app.delete("/cars/{id}", response_description="Delete a car")
async def delete_car(id: str):
    """
    Remove a single car record from the database.
    """
    delete_result = await car_collection.delete_one({"_id": ObjectId(id)})

    if delete_result.deleted_count == 1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail=f"car {id} not found")




#API for broker
#List broker's id
@app.get(
    "/brokers/ids",
    response_description="List all broker IDs",
)
async def list_broker_ids():
    """
    List all broker IDs in the database.
    """
    # Retrieve all broker records from the database
    brokers = await broker_collection.find().to_list(1000)

    # Extract IDs from broker records
    broker_ids = [str(broker["_id"]) for broker in brokers]

    return broker_ids

#create new broker
@app.post(
    "/brokers/",
    response_description="Add new broker",
    response_model=BrokerModel,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
async def create_broker(broker: BrokerModel = Body(...)):
    """
    Insert a new broker record.

    A unique `id` will be created and provided in the response.
    """
    new_broker = await broker_collection.insert_one(
        broker.model_dump(by_alias=True, exclude=["id"])
    )
    created_broker = await broker_collection.find_one(
        {"_id": new_broker.inserted_id}
    )
    return created_broker


#list all broker information
@app.get(
    "/brokers/",
    response_description="List all brokers",
    response_model=BrokerCollection,
    response_model_by_alias=False,
)
async def list_brokers():
    """
    List all of the broker data in the database.

    The response is unpaginated and limited to 1000 results.
    """
    
    return BrokerCollection(brokers=await broker_collection.find().to_list(1000))
 
#show broker by id
@app.get(
    "/brokers/{id}",
    response_description="Get a single broker",
    response_model=BrokerModel,
    response_model_by_alias=False,
)
async def show_broker(id: str):
    """
    Get the record for a specific broker, looked up by `id`.
    """
    
    if (broker := await broker_collection.find_one({"_id": ObjectId(id)})) is not None:
        return broker

    raise HTTPException(status_code=404, detail=f"broker {id} not found")

#update broker by id
@app.put(
    "/brokers/{id}",
    response_description="Update a broker",
    response_model=BrokerModel,
    response_model_by_alias=False,
)
async def update_broker(id: str, broker: UpdateBrokerModel = Body(...)):
    """
    Update individual fields of an existing broker record.

    Only the provided fields will be updated.
    Any missing or `null` fields will be ignored.
    """
    broker = {
        k: v for k, v in broker.model_dump(by_alias=True).items() if v is not None
    }

    if len(broker) >= 1:
        update_result = await broker_collection.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": broker},
            return_document=ReturnDocument.AFTER,
        )
        if update_result is not None:
            return update_result
        else:
            raise HTTPException(status_code=404, detail=f"broker {id} not found")

    # The update is empty, but we should still return the matching document:
    if (existing_broker := await broker_collection.find_one({"_id": id})) is not None:
        return existing_broker

    raise HTTPException(status_code=404, detail=f"broker {id} not found")

#delete_broker by id
@app.delete("/brokers/{id}", response_description="Delete a broker")
async def delete_broker(id: str):
    """
    Remove a single broker record from the database.
    """
    delete_result = await broker_collection.delete_one({"_id": ObjectId(id)})

    if delete_result.deleted_count == 1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail=f"broker {id} not found")













