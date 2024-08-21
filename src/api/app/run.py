import uvicorn
from fastapi import FastAPI

from src.api.routers.clients.client import clients_router


def create_server(lifespan=None):
    server = FastAPI(lifespan=lifespan,
                     title="APPLICATION",
                     )
    server.include_router(clients_router)

    return server

server = create_server()

if __name__ == "__main__":
    uvicorn.run("run:server",
                host="localhost",
                port=9192,
                lifespan="on",
                log_level="debug",
                reload=False)