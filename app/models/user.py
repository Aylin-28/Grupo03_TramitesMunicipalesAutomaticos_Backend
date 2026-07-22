from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String, nullable=False)

    email = Column(String, unique=True, nullable=False)

    password = Column(String, nullable=False)

    document_type = Column(String, nullable=False)

    document_number = Column(String, unique=True, nullable=False)

    role = Column(String, nullable=False, default="user")

    chats = relationship("Chat", back_populates="user")

