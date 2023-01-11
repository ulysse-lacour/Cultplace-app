from typing import Any, Dict, Optional
from werkzeug import Response
from werkzeug.exceptions import HTTPException


class SerializationError(HTTPException):
    code = 422
    description = "Failed to serialize response"
    extra: Dict[str, Any] = {}

    def __init__(
        self,
        description: Optional[str] = None,
        response: Optional[Response] = None,
        extra: Dict[str, Any] = None
    ) -> None:
        if extra is not None:
            self.extra = extra

        super().__init__(description, response)
