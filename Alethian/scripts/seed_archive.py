import sys
import os
import uuid
import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app.db.session import SessionLocal
from app.db.models import Document, DocumentStatus, User, UserRole
from app.core.similarity import index_document
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed_database():
    db = SessionLocal()
    
    admin_id = str(uuid.uuid4())
    admin = User(
        id=admin_id,
        username="admin",
        email="admin@alethian.edu",
        hashed_password=pwd_context.hash("admin_secure_password"),
        full_name="System Admin",
        role=UserRole.admin
    )
    db.add(admin)
    
    docs = [
        {"title": "Theories of Everything", "author": "Alice Schmidt", "text": "This is a fundamental theory of physics."},
        {"title": "Biological Data", "author": "Bob Jones", "text": "Cells are the building block of life on earth."},
        {"title": "Machine Learning in 2026", "author": "Eve Johnson", "text": "Deep neural networks are standard across industry applications."},
    ]
    
    for d in docs:
        doc_id = str(uuid.uuid4())
        doc = Document(
            id=doc_id,
            title=d["title"],
            author=d["author"],
            filename="archive_dummy.pdf",
            status=DocumentStatus.complete,
            upload_date=datetime.datetime.now(datetime.timezone.utc),
            is_archived=True
        )
        db.add(doc)
        db.flush()
        
        print(f"Indexing stored document {doc_id} into VDB...")
        index_document(doc_id, d["text"], title=d["title"])

    db.commit()
    print("Database seeding complete!")

if __name__ == "__main__":
    seed_database()
