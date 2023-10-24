# models.py

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class FamilyMember(Base):
    __tablename__ = 'family_members'
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    events = relationship("Event", back_populates="family_member")
    reminders = relationship("Reminder", back_populates="family_member")

class Contact(Base):
    __tablename__ = 'contacts'
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    phone = Column(String)

class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True)
    description = Column(String)
    date = Column(DateTime)
    family_member_id = Column(Integer, ForeignKey('family_members.id'))
    family_member = relationship("FamilyMember", back_populates="events")

class Reminder(Base):
    __tablename__ = 'reminders'
    id = Column(Integer, primary_key=True)
    text = Column(String)
    date = Column(DateTime)
    family_member_id = Column(Integer, ForeignKey('family_members.id'))
    family_member = relationship("FamilyMember", back_populates="reminders")
