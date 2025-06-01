from pydantic import BaseModel
from typing import List, Optional, Any

class CrawlTaskResponse(BaseModel):
    task_id: str
    status: str
    message: str
    courses: Optional[List[Any]] = None