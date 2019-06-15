import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

    @property
    def serialize(self):
        return{
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'picture': self.picture
            }


class Cloth(Base):
    __tablename__ = 'cloth'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable formate"""
        return {
            'name': self.name,
            'id': self.id
            }


class Model(Base):
    __tablename__ = 'model'

    name = Column(String(100), nullable=False)
    id = Column(Integer, primary_key=True)
    price = Column(String(250))
    color = Column(String(10))
    pic = Column(String(20))
    brand = Column(String(100))
    model_id = Column(Integer, ForeignKey('cloth.id'))
    cloth = relationship(Cloth)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable formate"""
        return{
            'name': self.name,
            'price': self.price,
            'id': self.id,
            'color': self.color,
            'pic': self.pic,
            'brand':self.brand,
            'model_id': self.model_id
            }

engine = create_engine('sqlite:///clothsdata.db')

Base.metadata.create_all(engine)
