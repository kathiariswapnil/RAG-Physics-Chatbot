from Database_operations.db import engine
from Database_operations.models import Base


Base.metadata.create_all(bind=engine)
print("Tables created successfully.")