from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from pymongo import MongoClient
from bson import ObjectId
import asyncio

from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
import os

app = FastAPI()


load_dotenv()
# 定義一個資料模型


class userList(BaseModel):
    name: Optional[str] = None  # name 是可選的
    idNumber: Optional[str] = None  # idNumber 是可選的
    lineId: Optional[str] = None
    tel: Optional[str] = None
    healthMeasurement: Optional[int] = 0  # 默認為 0，但也可以不填
    healthEducation: Optional[int] = 0  # 默認為 0，但也可以不填
    exercise: Optional[int] = 0  # 默認為 0，但也可以不填

    class Config:
        # 設置 ORM 模式以便於處理 MongoDB 的 ObjectId
        json_encoders = {
            ObjectId: str
        }


# 資料庫
dbName = os.getenv("dbName")
collectionName = os.getenv("collectionName")
client = MongoClient(
    os.getenv("client"))
database = client[dbName]
collection = database[collectionName]

# 確認資料庫連結成功與否

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允許的來源，可以是特定的域名，如 ["https://example.com"]
    allow_credentials=True,
    allow_methods=["*"],  # 允許的 HTTP 方法，如 ["GET", "POST"]
    allow_headers=["*"],  # 允許的 HTTP 標頭，如 ["Authorization", "Content-Type"]
)

async def connect_to_mongo():
    try:
        # 測試 ping 值，若沒有回應就會走 except 回報未連結
        await asyncio.to_thread(client.admin.command, 'ping')
        print("MongoDB 連接成功")
    except Exception as e:
        print(f"MongoDB 連接失敗: {e}")

# 開始時執行確認函式


async def lifespan(app: FastAPI):
    # 在應用啟動時執行
    await connect_to_mongo()
    yield
    # 在應用關閉時執行
    client.close()
    
@app.get("/keep/")
async def keep():
    return "OK"


@app.post("/add_user/", response_model=userList)
async def add_user(user: userList):
    # 將 user 物件轉換成字典
    user_dict = user.dict(by_alias=True)
    # 插入資料到資料庫
    result = collection.insert_one(user_dict)
    # 將 MongoDB 回傳的 `_id` 設置到回傳的資料中
    user_dict["_id"] = str(result.inserted_id)
    return user_dict


# 比對是否有此人

@app.get("/search/")
async def matching_id(user: userList):
    idNumber = user.idNumber
    result = collection.find_one({"idNumber": idNumber})
    if result:
        result['_id'] = str(result['_id'])  # 轉換 ObjectId
        return result
    else:
        raise HTTPException(status_code=404, detail="未找到符合的 ID")
    
@app.get("/searchLineID/")
async def matching_id(user: userList):
    lineId = user.lineId
    result = collection.find_one({"lineId": lineId})
    if result:
        result['_id'] = str(result['_id'])  # 轉換 ObjectId
        return result
    else:
        raise HTTPException(status_code=404, detail="未找到符合的 ID")
    
    
@app.post("/linkLineID/")
async def link_line_id(user: userList):
    idNumber = user.idNumber
    lineId = user.lineId
    
    resultLineId = collection.find_one({"lineId": lineId})
    resultIdNumber = collection.find_one({"idNumber": idNumber})
    
    if resultLineId:
        raise HTTPException(status_code=400, detail="該 Line ID 已經存在，無法重複註冊")
    if resultIdNumber:
        # 如果已經有相同的 idNumber，更新 lineId
        update_result = collection.update_one(
            {"idNumber": idNumber},  # 查找有相同 idNumber 的記錄
            {"$set": {"lineId": lineId}}  # 設置新的 lineId
        )
        
        if update_result.matched_count > 0:
            return {"message": "Line ID 已成功綁定到現有帳號"}
        else:
            raise HTTPException(status_code=404, detail="未找到符合的 ID")
    else:
        raise HTTPException(status_code=400, detail="無參加此活動~")

# 更新++
@app.put("/add/{item}", response_model=userList)
async def add_item(item: str, data: userList):
    if item not in ["healthMeasurement", "healthEducation", "exercise"]:
        raise HTTPException(status_code=400, detail="無效的欄位名稱")

    update_result = collection.find_one_and_update(
        {"lineId": data.lineId},
        {"$inc": {item: 1}},  # 動態更新指定欄位
        return_document=True  # 返回更新後的文件
    )
    if update_result:
        update_result["_id"] = str(update_result["_id"])  # 轉換 ObjectId
        return update_result
    else:
        raise HTTPException(status_code=404, detail="未找到符合的 ID")
# 建立新的 userList

# 刪除 ToDo
@app.delete("/user/{id}", response_model=userList)
async def delete_todo(id: str):
    result = collection.delete_one({"idNumber": id})

    if result.deleted_count > 0:
        raise HTTPException(status_code=200, detail="刪除成功")
    else:
        raise HTTPException(status_code=404, detail="請確認 ID")

@app.delete("/logout", response_model=userList)
async def logout(user: userList):

    result = collection.find_one_and_update(
        {"lineId": user.lineId},
        {"$set": {"lineId": none}},  # 動態更新指定欄位
        return_document=True  # 返回更新後的文件
    )
    
    if result:
        raise HTTPException(status_code=200, detail="刪除成功")
    else:
        raise HTTPException(status_code=404, detail="刪除失敗，請聯絡管理員")
        
    
#uvicorn main:app --host 0.0.0.0 --port 8000