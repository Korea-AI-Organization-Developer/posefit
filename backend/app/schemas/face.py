from pydantic import BaseModel


class FaceRegisterRequest(BaseModel):
    image: str  # base64 이미지


class FaceLoginRequest(BaseModel):
    image: str  # base64 이미지


class FaceLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    nickname: str
