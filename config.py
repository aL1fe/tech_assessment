from pydantic_settings import BaseSettings
from pydantic import BaseModel


class CameraConfig(BaseModel):
    fps: int


class Settings(BaseSettings):
    
    BASE_DELAY: int = 1
    MAX_DELAY: int = 30
    STABLE_THRESHOLD: int = 30

    CAMERA_CFG: dict[str, CameraConfig] = {
        "cam_01": CameraConfig(fps=15),
        "cam_02": CameraConfig(fps=15),
        "cam_03": CameraConfig(fps=10),
        "cam_04": CameraConfig(fps=10),
    }
    
    class Config:
        env_file = ".env"

settings = Settings()
