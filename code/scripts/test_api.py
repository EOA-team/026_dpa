from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello from Drone Station API"}

# Run with: python -m uvicorn code.scripts.test_api:app --host 0.0.0.0 --port 8000