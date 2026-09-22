"""
Pipeline configuration, read from environment variables
(see .env.example).
"""
import os

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "dbname": os.getenv("POSTGRES_DB", "transit_data_hub"),
    "user": os.getenv("POSTGRES_USER", "transit_user"),
    "password": os.getenv("POSTGRES_PASSWORD", "transit_pass"),
}

DATA_DIR = os.getenv("DATA_DIR", "data/raw")
