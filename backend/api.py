import uvicorn
from app import app
from app.config import config

if __name__ == "__main__":
    uvicorn.run(app, host=config.HOST, port=config.PORT)