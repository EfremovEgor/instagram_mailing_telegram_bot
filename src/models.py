from sqlalchemy import Column, Integer, String, DateTime, null, Boolean
from database import Base
from sqlalchemy.dialects.postgresql import TEXT


class MailingTarget(Base):
    __tablename__ = "mailing_targets"

    target_id = Column(Integer, primary_key=True)
    status = Column(String, nullable=False, default="PENDING")
    username = Column(String, nullable=False)
    worker = Column(String, nullable=True, default=None)
    first_name = Column(String, nullable=True, default=None)
    sex = Column(String, nullable=False, default="MALE")
    was_answered_by_target = Column(Boolean, nullable=True, default=False)
    done_at = Column(DateTime(timezone=True), nullable=True, default=None)


class BaseMessage(object):
    id = Column(Integer, primary_key=True)
    worker = Column(String, nullable=True)
    message = Column(TEXT, nullable=True)
    sender_username = Column(String, nullable=False)


class NewMessage(BaseMessage, Base):
    __tablename__ = "new_messages"
    status = Column(String, nullable=False, default="PENDING")
    answer = Column(TEXT, nullable=True, default=None)
    notified = Column(Boolean, nullable=False, default=False)


class MessageThread(BaseMessage, Base):
    __tablename__ = "message_threads"
    thread_username = Column(String, nullable=False)


class Worker(Base):
    __tablename__ = "workers"

    worker_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    account_name = Column(String, nullable=False)
    account_password = Column(String, nullable=False)


class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, unique=True)
