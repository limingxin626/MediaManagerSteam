import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.new_models import create_new_tables

if __name__ == "__main__":
    print("Creating new database tables...")
    create_new_tables()
    print("New database tables created successfully!")
