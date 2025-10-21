from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True) 
    #  if a user matches with another user, we can just reveal their email for contact
    #  this way we don't have to build a messaging system
    #  i was thinking of using phone numbers but that raises privacy concerns
    password_hash = Column(String, nullable=False)
    school = Column(String, nullable=True)

    listings = relationship("Listing", back_populates="lister_user")
