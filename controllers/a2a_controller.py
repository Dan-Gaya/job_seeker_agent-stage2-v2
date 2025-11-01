# # controllers/a2a_controller.py
# from fastapi import APIRouter, Request
# from fastapi.responses import JSONResponse
# from models.a2a import JSONRPCRequest, JSONRPCResponse, TaskResult
# from pydantic import ValidationError
# from agents.jobseeker_agent import JobSeekerAgent

# router = APIRouter()
# agent = JobSeekerAgent()

# @router.post("/a2a/jobseeker")
# async def a2a_endpoint(request: Request):
#     body = await request.json()
#     if body.get("jsonrpc") != "2.0" or "id" not in body:
#         return JSONResponse(status_code=400, content={
#             "jsonrpc": "2.0",
#             "id": body.get("id"),
#             "error": {"code": -32600, "message": "Invalid Request: jsonrpc must be '2.0' and id is required"}
#         })
#     try:
#         rpc_request = JSONRPCRequest(**body)
#     except ValidationError as e:
#         return JSONResponse(status_code=400, content={
#             "jsonrpc": "2.0",
#             "id": body.get("id"),
#             "error": {"code": -32602, "message": "Invalid params", "data": str(e)}
#         })

#     # parse input
#     messages = []
#     context_id = None
#     task_id = None
#     config = None

#     if rpc_request.method == "message/send":
#         messages = [rpc_request.params.message]
#         config = rpc_request.params.configuration
#     else:  # execute
#         messages = rpc_request.params.messages
#         context_id = rpc_request.params.contextId
#         task_id = rpc_request.params.taskId

#     try:
#         result: TaskResult = await agent.process_messages(messages=messages, context_id=context_id, task_id=task_id, config=config)
#         response = JSONRPCResponse(id=rpc_request.id, result=result)
#         # return model dict (Pydantic)
#         return response.model_dump()
#     except Exception as e:
#         return JSONResponse(status_code=500, content={
#             "jsonrpc": "2.0",
#             "id": rpc_request.id,
#             "error": {"code": -32603, "message": "Internal error", "data": str(e)}
#         })

# controllers/a2a_controller.py
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from models.a2a import JSONRPCRequest, JSONRPCResponse, TaskResult
from agents.jobseeker_agent import JobSeekerAgent
from utils.a2a_response import create_error_response, A2AErrorCode
import traceback

router = APIRouter()
agent = JobSeekerAgent()

@router.post("/a2a/jobseeker")
async def a2a_endpoint(request: Request):
    body = await request.json()
    # basic JSON-RPC validation
    if body.get("jsonrpc") != "2.0" or "id" not in body:
        return JSONResponse(status_code=400, content=create_error_response(body.get("id"), A2AErrorCode.INVALID_REQUEST, "Invalid Request: jsonrpc must be '2.0' and id is required"))

    try:
        rpc_request = JSONRPCRequest(**body)
    except ValidationError as e:
        return JSONResponse(status_code=400, content=create_error_response(body.get("id"), A2AErrorCode.INVALID_PARAMS, "Invalid params", {"details": str(e)}))

    # parse input
    messages = []
    context_id = None
    task_id = None
    config = None

    if rpc_request.method == "message/send":
        messages = [rpc_request.params.message]
        config = rpc_request.params.configuration
    else:  # execute
        messages = rpc_request.params.messages
        context_id = rpc_request.params.contextId
        task_id = rpc_request.params.taskId

    try:
        result: TaskResult = await agent.process_messages(messages=messages, context_id=context_id, task_id=task_id, config=config)
        response = JSONRPCResponse(id=rpc_request.id, result=result)
        return response.model_dump()  # pydantic -> dict
    except Exception as e:
        # internal error: return A2A error envelope
        tb = traceback.format_exc()
        return JSONResponse(status_code=500, content=create_error_response(rpc_request.id, A2AErrorCode.INTERNAL_ERROR, "Internal error", {"details": str(e), "trace": tb}))
