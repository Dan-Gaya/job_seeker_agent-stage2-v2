# utils/a2a_response.py
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import uuid4
from models.a2a import A2AMessage, MessagePart, Artifact, TaskResult, TaskStatus
from datetime import datetime

class A2AErrorCode(Enum):
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

def create_error_response(request_id: str, code: A2AErrorCode, message: str, data: Optional[Dict]=None) -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": code.value,
            "message": message,
            "data": data or {}
        }
    }

def agent_text_part(text_str: str) -> MessagePart:
    """
    Wrap a plain string into a structured text dict for A2A.
    e.g. {"message": "..."} — consistent with A2A spec's structured parts
    """
    return MessagePart(kind="text", text={"message": text_str})

def make_agent_message(text_str: str, task_id: str) -> A2AMessage:
    return A2AMessage(
        role="agent",
        parts=[agent_text_part(text_str)],
        taskId=task_id
    )

def make_artifact(name: str, part_kind: str, payload: Any) -> Artifact:
    # For structured payloads, put into `data` for kind=data, or text for text-kind (structured)
    if part_kind == "data":
        mp = MessagePart(kind="data", data=payload)
    elif part_kind == "text":
        mp = MessagePart(kind="text", text={"message": payload})
    else:
        mp = MessagePart(kind=part_kind, data=payload)
    return Artifact(name=name, parts=[mp])

def make_task_result(task_id: str, context_id: str, state: str, agent_message: A2AMessage, artifacts: List[Artifact], history: List[A2AMessage]) -> TaskResult:
    status = TaskStatus(state=state, timestamp=datetime.utcnow().isoformat() + "Z", message=agent_message)
    return TaskResult(id=task_id, contextId=context_id, status=status, artifacts=artifacts, history=history)
