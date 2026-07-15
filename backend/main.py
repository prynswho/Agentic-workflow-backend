
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.pipelines import router as pipelines_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pipelines_router)

@app.get('/')
def read_root():
    return {'Ping': 'Pong'}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
