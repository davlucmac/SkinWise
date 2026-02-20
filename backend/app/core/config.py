import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://skinwise:skinwise@localhost:5432/skinwise")
BASIC_ADMIN_USER = os.getenv("BASIC_ADMIN_USER", "admin")
BASIC_ADMIN_PASSWORD = os.getenv("BASIC_ADMIN_PASSWORD", "admin")
