from sqlalchemy.orm import Session as SQLAlchemySession


class BaseRepository:
    def __init__(self, db_session: SQLAlchemySession):
        self.db_session = db_session
