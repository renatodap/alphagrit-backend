from pydantic import BaseModel


class PostUploadIn(BaseModel):
    program_id: int
    post_id: int
    filename: str


class MetricUploadIn(BaseModel):
    metric_id: int
    filename: str

