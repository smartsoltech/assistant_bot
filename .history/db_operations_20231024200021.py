# db_operations.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, FamilyMember, Contact, Event, Reminder

DATABASE_URL = 'sqlite:///family_assistant.db'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)

def save_contact(name, phone):
    session = Session()
    new_contact = Contact(name=name, phone=phone)
    session.add(new_contact)
    session.commit()
    session.close()

# Дополнительные функции для работы с базой данных (добавление напоминаний, событий и т.д.) могут быть добавлены здесь
