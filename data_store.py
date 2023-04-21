# импорты
import sqlalchemy as sq
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import Session


# схема БД
metadata = MetaData()
Base = declarative_base()

class Viewed(Base):
    __tablename__ = 'viewed'
    profile_id = sq.Column(sq.Integer, primary_key=True)
    worksheet_id = sq.Column(sq.Integer, primary_key=True)


# добавление записи в бд

engine = create_engine(db_url_object)
Base.metadata.create_all(engine)
with Session(engine) as session:
    to_bd = Viewed(profile_id=1, worksheet_id=1)
    session.add(to_bd)
    session.commit()

# извлечение записей из БД

engine = create_engine(db_url_object)
with Session(engine) as session:
    from_bd = session.query(Viewed).filter(Viewed.profile_id==1).all()
    for item in from_bd:
        print(item.worksheet_id)
