import json
import time

import aiohttp
import jwt
from fastapi import FastAPI, Request, Response, HTTPException, status
from jwt import PyJWTError
from starlette.responses import JSONResponse

SECRET_KEY = "Cj9Ndq9c2mSPaI6zHHkdWwEXpudGUlYf1234567890abcdefgijklmnopqrstuvwxyz"
ALGORITHM = "HS512"

app = FastAPI()

with open('services_config.json', 'r') as config_file:
    gateway_config = json.load(config_file)


def decode_jwt(token: str, user_id: str = None) -> dict:
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if decoded_token["exp"] < time.time():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token expired")

        if user_id and decoded_token.get("user_id") != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid user ID")

        token_type = decoded_token.get('token_type')
        if token_type != 'access':
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

        return {"payload": decoded_token}
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )


@app.api_route("/{public_path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway_route(public_path: str, request: Request):
    service_config = None
    for route in gateway_config["routes"]:
        if public_path == route["public_path"]:
            service_config = route
            break

    if not service_config:
        raise HTTPException(status_code=404, detail="Service not found")

    if service_config.get("required_validation_token"):
        if not (auth_header := request.headers.get("Authorization")):
            raise HTTPException(status_code=401, detail="Authorization header is missing")

        token = auth_header.split(" ")[1] if len(auth_header.split(" ")) > 1 else None  # Created by GPT
        if not token:  # Created by GPT
            raise HTTPException(status_code=401, detail="Token not provided")  # Created by GPT

        user_id = request.headers.get("X-User-ID")  # Created by GPT
        decode_jwt(token, user_id)  # Created by GPT

    call_headers = {}

    method = request.method

    if request.headers.get("content-type") == "application/json":
        body = await request.json()
    else:
        body = await request.body()

    full_url = f"{service_config['service_url']}/{public_path}"

    async with aiohttp.ClientSession() as session:
        async with session.request(method, full_url, headers=call_headers,
                                   json=body if isinstance(body, dict) else None) as response:
            try:
                response_content = await response.json()
                return JSONResponse(content=response_content, status_code=response.status)
            except ValueError:
                response_content = await response.read()
                return Response(content=response_content, status_code=response.status)
