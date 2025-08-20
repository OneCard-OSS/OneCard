import os 
from dotenv import load_dotenv
import redis
import logging

load_dotenv()

def redis_config():
    REDIS_HOST=os.getenv("REDIS_HOST")
    REDIS_PORT=int(os.getenv("REDIS_PORT"))
    REDIS_DATABASE=int(os.getenv("REDIS_DATABASE"))
    
    try:
        rd = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DATABASE)
        logging.info("Redis Connected Successfully")
        return rd
    except redis.ConnectionError as ce:
        raise ce
    