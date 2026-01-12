import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import Base, engine

print("Dropping all tables...")
# Drop all tables defined in Base (User, Organization, etc.)
from sqlalchemy import MetaData

# Reflect all existing tables from the database to ensure we drop everything,
# including tables that might not be defined in the current models (ghost tables).
metadata = MetaData()
metadata.reflect(bind=engine)
metadata.drop_all(bind=engine)
print("All tables dropped.")
