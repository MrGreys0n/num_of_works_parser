import asyncio
import time

from dotenv import load_dotenv
from parser import Parser
from datetime import datetime


async def configure() -> None:
    load_dotenv()


async def main() -> None:
    try:
        parser = Parser()
        parser.execute()
    except (Exception,) as e:
        print(f"Exception: {e}")


if __name__ == "__main__":
    asyncio.run(configure())
    asyncio.run(main())
    while True:
        now = datetime.now()
        print(now)
        if now.minute < 10:
            asyncio.run(main())
            time.sleep(3000)
        else:
            time.sleep(300)
