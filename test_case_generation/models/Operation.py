from typing import Optional, Dict, List, Any


class Operation:
    """
    Описывает одну операцию OpenAPI (метод, путь, параметры, requestBody, responses).
    """

    def __init__(
            self,
            method: str,
            path: str,
            summary: str = '',
            description: str = '',
            operation_id: str = '',
            parameters: Optional[List[Dict[str, Any]]] = None,
            request_body: Optional[Dict[str, Any]] = None,
            responses: Optional[Dict[str, Any]] = None,
    ):
        self.method = method.upper()
        self.path = path
        self.summary = summary
        self.description = description
        self.operation_id = operation_id
        self.parameters = parameters if parameters else []
        self.request_body = request_body if request_body else {}
        self.responses = responses if responses else {}

    def __repr__(self) -> str:
        return (
            f"Operation(method={self.method}, path={self.path}, "
            f"summary={self.summary}, operation_id={self.operation_id}, "
            f"params={len(self.parameters)}, request_body={bool(self.request_body)}, "
            f"responses={list(self.responses.keys())})"
        )