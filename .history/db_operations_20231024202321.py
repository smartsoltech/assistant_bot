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
    
def add_family_member(name):
    session = Session()
    member = FamilyMember(name=name)
    session.add(member)
    session.commit()
    session.close()
    return member.id

def add_event(description, date, family_member_id):
        # Преобразуем строку даты в объект datetime
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    session = Session()
    event = Event(description=description, date=date, family_member_id=family_member_id)
    session.add(event)
    session.commit()
    session.close()

def add_reminder(text, date, family_member_id):
    session = Session()
    reminder = Reminder(text=text, date=date, family_member_id=family_member_id)
    session.add(reminder)
    session.commit()
    session.close()
# Дополнительные функции для работы с базой данных (добавление напоминаний, событий и т.д.) могут быть добавлены здесь
