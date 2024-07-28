from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.orm import relationship

# from sqlalchemy_imageattach.entity import Image, image_attachment
from config.Database import Base


class Parent(Base):
    __tablename__ = "parents"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    age = Column(Integer)
    address = Column(String)
    city = Column(String)
    country = Column(String)
    pincode = Column(String)
    # Need to use remote storage like Amazon s3, storing image in db is a bad approach
    profile_photo = Column(String)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, default=text("now()"))
    updated_at = Column(
        DateTime, nullable=False, onupdate=text("now()"), default=text("now()")
    )

    children = relationship("Child", back_populates="parent")

    def __repr__(self):
        return (
            f"<Parent(id={self.id}, email={self.email}, is_active={self.is_active}, "
            f"first_name={self.first_name}, last_name={self.last_name}, age={self.age}, "
            f"address={self.address}, city={self.city}, country={self.country}, "
            f"pincode={self.pincode}, created_at={self.created_at}, updated_at={self.updated_at})>"
        )


class Child(Base):
    __tablename__ = "children"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    birth_date = Column(DateTime)
    parent_id = Column(Integer, ForeignKey("parents.id"))
    created_at = Column(DateTime, nullable=False, default=text("now()"))
    updated_at = Column(
        DateTime, nullable=False, onupdate=text("now()"), default=text("now()")
    )
    # relation
    parent = relationship("Parent", back_populates="children")

    def __repr__(self):
        return (
            f"<Child(id={self.id}, name={self.name}, birth_date={self.birth_date}, "
            f"parent_id={self.parent_id}, created_at={self.created_at}, updated_at={self.updated_at})>"
        )
