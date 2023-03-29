import typing
from flask import Request
from sqlalchemy import Column, Sequence
from sqlalchemy import SMALLINT
from flask_login import UserMixin
from app.ext import db, login_manager
from app.utils import get_unix_time_tuple
from uuid import uuid4


class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = Column(
        db.Integer,
        Sequence("user_id_seq", start=1, increment=1),
        primary_key=True
    )
    identifier = Column(
        db.String(32), nullable=False, unique=True, comment="用户的标识符，在某些情况不适合用id，会用此字段"
    )
    email = Column(db.String(64), nullable=False, unique=True)
    password = Column(db.String(64), nullable=True)
    create_at = Column(db.Integer, nullable=False, comment="创建时间")

    def __init__(
        self,
        email: typing.Optional[str],
        password: typing.Optional[str],
    ) -> None:
        assert email
        # assert password
        self.identifier = uuid4().hex
        self.email = email
        self.password = password
        self.create_at = get_unix_time_tuple(millisecond=True)

    def to_json(self) -> typing.Dict[str, typing.Any]:
        """  将用户信息组装成字典
        """
        payload: typing.Dict[str, typing.Any] = {
            "identifier": self.identifier,
            "email": self.email or "",
        }
        return payload

    @staticmethod
    def transform_password(password: str) -> str:
        from passlib.hash import hex_md5
        return hex_md5.hash(password)

    @login_manager.user_loader
    def user_loader(user_identifier: str) -> typing.Optional["User"]:
        print(f" user_loader callback: {user_identifier}")
        return User.query.filter_by(identifier=user_identifier).first()

class Conversation(db.Model):
    __tablename__ = "conversation"
    
    cov_id = Column(
        db.Integer,
        Sequence("conv_id_seq", start=1, increment=1),
        primary_key=True
    )
    identifier = Column(
        db.String(32), nullable=False, unique=True, comment="会话的标识符，在某些情况不适合用id，会用此字段"
    )
    user_id = Column(
        db.Integer, nullable=False, comment="用户"
    )
    chats = db.relationship("ChatRecord", backref="conversation", lazy="dynamic")
    create_at = Column(db.Integer, nullable=False, comment="创建时间")
    
    def __init__(self, user: User, identifier: typing.Optional[str] = None) -> None:
        self.user_id = user.id
        self.identifier = identifier or uuid4().hex
        self.create_at = get_unix_time_tuple(millisecond=True)


class ChatRecord(db.Model):
    __tablename__ = "chat_record"

    chat_id = Column(
        db.Integer,
        Sequence("chat_id_seq", start=1, increment=1),
        primary_key=True
    )
    user_id = Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    conversation = Column(db.Integer, db.ForeignKey("conversation.cov_id"), nullable=False)
    content = Column(db.Text, nullable=False, comment="聊天内容")
    role = Column(SMALLINT, nullable=False, comment="角色，0表示用户，1表示机器人")
    create_at = Column(db.Integer, nullable=False, comment="创建时间")

    
    def __init__(
        self,
        user: User,
        content: str,
        conversation: Conversation,
        response_chat: typing.Optional['ChatRecord'] = None # 没有这个参数表示用户发起的聊天，有这个参数表示机器人回复的聊天
    ) -> None:
        self.user_id = user.id
        self.content = content
        self.conversation = conversation.cov_id
        self.create_at = get_unix_time_tuple(millisecond=True)
        self.role = 0 if response_chat else 1


    def to_json(self) -> typing.Dict[str, typing.Any]:
        """  将用户信息组装成字典
        """
        payload: typing.Dict[str, typing.Any] = {
            "chat_id": self.chat_id,
            "conversation": self.conversation,
            "content": self.content,
            "create_at": self.create_at,
            "role": self.role,
        }
        return payload