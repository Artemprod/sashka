import uvicorn

from configs.main_api_gateway import main_api_gateway_configs
from src.web.loader.server_creater import create_server

server = create_server()

if __name__ == "__main__":
    uvicorn.run("main:server",
                host=main_api_gateway_configs.host,
                port=main_api_gateway_configs.port,
                lifespan=main_api_gateway_configs.lifespan,
                log_level=main_api_gateway_configs.log_level,
                reload=main_api_gateway_configs.reload)
