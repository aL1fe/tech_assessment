from pydantic_settings import BaseSettings
from pydantic import BaseModel


class CameraConfig(BaseModel):
    fps: int


class Settings(BaseSettings):
    # Cameras config
    BASE_DELAY: int = 1  # Base delay before reconnect (s)
    MAX_DELAY: int = 30   # Max delay before reconnect (s)
    MAX_RECONNECT: int = 10

    CAMERA_CFG: dict[str, CameraConfig] = {
        "cam_01": CameraConfig(fps=15),
        "cam_02": CameraConfig(fps=15),
        "cam_03": CameraConfig(fps=10),
        "cam_04": CameraConfig(fps=10),
    }

    # Frame config
    WIDTH: int= 3840
    HEIGHT: int = 2160
    CHANNELS: int = 3
    FRAME_SUBSAMPLE: int = 100  # TODO change to 6
    
    class Config:
        env_file = ".env"

settings = Settings()
