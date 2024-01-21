from fastapi import FastAPI, Response

from ci_server import CIDataManager

app = FastAPI()
data_manager = CIDataManager()


@app.get("/")
def read_root():
    return Response("Server is running.")


@app.get("/runs")
def read_runs():
    return data_manager.get_runs()
