import uvicorn

from src.web.loader.server_creater import create_server

server = create_server()

if __name__ == "__main__":
    uvicorn.run("main:server",
                host="localhost",
                port=9194,
                lifespan="on",
                log_level="debug",
                reload=True)