import asyncio
import sys
from typing import Annotated

import uvicorn
from fastapi import Depends, FastAPI, Response

from ci_manager import CIDataManager, ci_service

app = FastAPI()


def get_data_manager():
    return CIDataManager()


@app.get("/")
def read_root():
    return Response("Server is running.")


@app.get("/runs")
def read_runs(data_manager: Annotated[CIDataManager, Depends(get_data_manager)]):
    runs = data_manager.get_runs()
    return {"total": len(runs), "data": runs}


@app.get("/run/{commit_hash}")
def read_run(
    commit_hash: str, data_manager: Annotated[CIDataManager, Depends(get_data_manager)]
):
    # Search for specific commit in data_manager's records
    for run in data_manager.get_runs():
        if run["id"] == commit_hash:
            return run


async def main() -> None:
    data_manager = CIDataManager()
    repo_path = sys.argv[1]
    server_port = sys.argv[2].lstrip(":")
    server_url = f"http://localhost:{server_port}/step/trigger"

    if not server_url.startswith("http"):
        server_url = f"http://{server_url}"

    # start the CI service as a background task
    asyncio.create_task(ci_service(repo_path, server_url, data_manager))
    uvicorn_config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=9000,
        loop="asyncio",
    )
    server = uvicorn.Server(config=uvicorn_config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
