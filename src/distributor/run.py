import asyncio

from src.distributor.app.loader.create_app import create_app


async def main():
    """"""
    app = create_app()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
