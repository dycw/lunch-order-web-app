from uvicorn import run

if __name__ == "__main__":
    run("backend.app:app", reload=True)
