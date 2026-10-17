import ipaddress

from pydantic import BaseModel, Field, field_validator


class CameraBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    stream_url: str
    # Position on the barn map as a fraction (0..1) of the image width/height,
    # so markers stay in place no matter how large the image is displayed.
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)


class Camera(CameraBase):
    id: int
