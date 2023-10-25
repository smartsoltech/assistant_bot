from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class FamilyMember(Base):
    __tablename__ = 'family_members'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)

class Contact(Base):
    __tablename__ = 'contacts'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('family_members.id'))  # Ссылка на пользователя, который добавил контакт
    phone_number = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)

    def __repr__(self):
        return f"<Contact(id={self.id}, phone_number={self.phone_number}, first_name={self.first_name}, last_name={self.last_name})>"


class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    description = Column(String)
    date = Column(DateTime)
    family_member_id = Column(Integer, ForeignKey('family_members.id'))
    family_member = relationship('FamilyMember')

class Reminder(Base):
    __tablename__ = 'reminders'

    id = Column(Integer, primary_key=True)
    description = Column(String)  # убедитесь, что этот атрибут есть
    date = Column(DateTime)
    family_member_id = Column(Integer, ForeignKey('family_members.id'))
    

engine = create_engine('sqlite:///assistant_bot.db')
Session = sessionmaker(bind=engine)

