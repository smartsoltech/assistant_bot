# db_operations.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, FamilyMember, Contact, Event, Reminder
from datetime import datetime

DATABASE_URL = 'sqlite:///family_assistant.db'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(engine)

def add_reminder_to_db(date, description, member_id):
    session = Session()
    new_reminder = Reminder(
        date=date,
        description=description,
        family_member_id=member_id
    )
    session.add(new_reminder)
    session.commit()
    session.close()
    
def add_contact(user_id, phone_number, first_name, last_name):
    session = Session()
    contact = Contact(user_id=user_id, phone_number=phone_number, first_name=first_name, last_name=last_name)
    session.add(contact)
    session.commit()
    session.close()

def add_family_member(name):
    session = Session()
    member = FamilyMember(name=name)
    session.add(member)
    session.commit()
    return member.id
    session.close()

def add_event(description, date_str, family_member_id):
        # Преобразуем строку даты в объект datetime
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    
    session = Session()
    event = Event(description=description, date=date_obj, family_member_id=family_member_id)
    session.add(event)
    session.commit()
    session.close()
    
def get_family_member_by_name(name):
    session = Session()
    member = session.query(FamilyMember).filter_by(name=name).first()
    session.close()
    return member

def add_reminder(text, date, family_member_id):
    session = Session()
    reminder = Reminder(text=text, date=date, family_member_id=family_member_id)
    session.add(reminder)
    session.commit()
    session.close()
    
def get_family_members():
    session = Session()
    members = session.query(FamilyMember).all()
    session.close()
    return members

def find_contact_by_name_or_phone(name_or_phone):
    session = Session()
    if name_or_phone.isdigit():
        # Если пользователь ввел числа, ищем по последним цифрам телефона
        contacts = session.query(Contact).filter(Contact.phone.endswith(name_or_phone)).all()
    else:
        # Если пользователь ввел текст, ищем по имени контакта
        contacts = session.query(Contact).filter(Contact.name.ilike(f"%{name_or_phone}%")).all()
    session.close()
    return contacts
# Дополнительные функции для работы с базой данных (добавление напоминаний, событий и т.д.) могут быть добавлены здесь

def get_reminders_by_family_member(member_id):
    session = Session()
    reminders = session.query(Reminder).filter_by(family_member_id=member_id).all()
    session.close()
    return reminders