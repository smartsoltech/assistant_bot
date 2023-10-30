# db_operations.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, FamilyMember, Contact, Event, Reminder
from datetime import datetime
from logger import log_decorator

DATABASE_URL = 'sqlite:///family_assistant.db'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


@log_decorator
def init_db():
    Base.metadata.create_all(engine)

@log_decorator
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
    
@log_decorator   
def add_contact(user_id, phone_number, first_name, last_name):
    session = Session()
    contact = Contact(user_id=user_id, phone_number=phone_number, first_name=first_name, last_name=last_name)
    session.add(contact)
    session.commit()
    session.close()

@log_decorator
def add_family_member(first_name, last_name, user_code, chat_id):
    session = Session()
    member = FamilyMember(
        first_name=first_name,
        last_name=last_name,
        user_code=user_code,
        chat_id=chat_id
    )
    session.add(member)
    session.commit()
    session.close()

@log_decorator
def add_event(description, date_input, family_member_id):
    if isinstance(date_input, str):
        date_obj = datetime.strptime(date_input, '%Y-%m-%d')
    else:
        date_obj = date_input
    
    session = Session()
    event = Event(description=description, date=date_obj, family_member_id=family_member_id)
    session.add(event)
    session.commit()
    session.close()

@log_decorator    
def get_family_member_by_name(name):
    session = Session()
    member = session.query(FamilyMember).filter_by(name=name).first()
    session.close()
    return member

@log_decorator
def add_reminder(text, date, family_member_id):
    session = Session()
    reminder = Reminder(description=text, date=date, family_member_id=family_member_id)
    session.add(reminder)
    session.commit()
    session.close()

@log_decorator    
def get_family_members():
    session = Session()
    members = session.query(FamilyMember).all()
    session.close()
    return members

@log_decorator
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

@log_decorator
def get_reminders_by_family_member(member_id):
    session = Session()
    reminders = session.query(Reminder).filter_by(family_member_id=member_id).all()
    session.close()
    return reminders

@log_decorator
def full_reset():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
def show_member_reminders():
    pass