from fastapi import FastAPI, HTTPException, Path, Body, Depends, Request
from pydantic import BaseModel, Field
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse
from typing import Optional

app = FastAPI()

# 仮のデータベース（辞書）
fake_db = {}

# 🔹 ユーザー登録リクエストモデル
class UserSignup(BaseModel):
    user_id: str = Field(..., min_length=6, max_length=20, pattern="^[a-zA-Z0-9]+$")
    password: str = Field(..., min_length=8, max_length=20, pattern="^[a-zA-Z0-9!@#$%^&*()_+=-]+$")

# 🔹 ユーザー更新リクエストモデル
class UserUpdate(BaseModel):
    password: Optional[str] = Field(None, min_length=8, max_length=20, pattern="^[a-zA-Z0-9!@#$%^&*()_+=-]+$")

# 🔹 アカウント削除リクエストモデル
class AccountDelete(BaseModel):
    confirm: bool

# 🔹 バリデーションエラーハンドリング
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    messages = []

    for error in errors:
        field = error["loc"][-1]  # フィールド名取得
        error_type = error["type"]

        if error_type == "value_error.missing":
            messages.append(f"{field}: 必須項目が含まれていない")
        elif "min_length" in error_type or "max_length" in error_type:
            messages.append(f"{field}: 長さちゃう")
        elif "str.regex" in error_type:
            messages.append(f"{field}: 文字種違う")

    return JSONResponse(status_code=400, content={"message": messages})

# 🔹 ユーザー登録 (POST /signup)
@app.post("/signup")
def signup(user: UserSignup):
    if not user.user_id or not user.password:
        raise HTTPException(status_code=400, detail={
            "message": "Account creation failed",
            "cause": "Required user_id and password"
        })

    if user.user_id in fake_db:
        raise HTTPException(status_code=400, detail={
            "message": "Account creation failed",
            "cause": "Already same user_id is used"
        })

    fake_db[user.user_id] = {"user_id": user.user_id, "password": user.password}

    return {
        "message": "Account successfully created",
        "user": {
            "user_id": user.user_id,
            "nickname": user.user_id  # 仮のニックネーム
        }
    }

# 🔹 ユーザー情報取得 (GET /users/{user_id})
@app.get("/users/{user_id}")
def get_user(user_id: str = Path(..., min_length=6, max_length=20)):
    user = fake_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"message": "User not found"})

    return {
        "user_id": user["user_id"],
        "nickname": user["user_id"]  # 仮のニックネーム
    }

# 🔹 ユーザー情報更新 (PATCH /users/{user_id})
@app.patch("/users/{user_id}")
def update_user(user_id: str, update_data: UserUpdate):
    user = fake_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"message": "User not found"})

    if update_data.password:
        user["password"] = update_data.password

    return {"message": "User information updated successfully"}

# 🔹 ユーザー削除 (POST /close)
@app.post("/close")
def close_account(data: AccountDelete = Body(...), user_id: str = Depends(lambda: "test_user")):
    if not data.confirm:
        raise HTTPException(status_code=400, detail={"message": "Account deletion confirmation required"})

    if user_id not in fake_db:
        raise HTTPException(status_code=404, detail={"message": "User not found"})

    del fake_db[user_id]
    return {"message": "Account successfully deleted"}
