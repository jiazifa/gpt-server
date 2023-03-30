# -*- coding: utf-8 -*-
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
        db.String(32),
        nullable=False,
        unique=True,
        comment="用户的标识符，在某些情况不适合用id，会用此字段"
    )
    email = Column(db.String(64), nullable=False, unique=True)
    password = Column(db.String(64), nullable=True)
    token = Column(db.String(64), nullable=True)
    create_at = Column(db.Integer, nullable=False, comment="创建时间")

    def __init__(
        self,
        email: typing.Optional[str],
        password: typing.Optional[str] = None,
    ) -> None:
        new_password = password or User.transform_password("123456")

        assert email

        self.identifier = uuid4().hex
        self.email = email
        self.password = new_password
        self.create_at = get_unix_time_tuple(millisecond=True)

    @staticmethod
    def get_user_by_email(email: str) -> typing.Optional["User"]:
        """Get the user object by email address.

        Args:
            email (str): The email address of the user.

        Returns:
            typing.Optional["User"]: The user object.
                None if the user does not exist.
        """
        user: typing.Optional['User'] = User.query.filter_by(email=email
                                                            ).first()
        return user

    def to_json(self) -> typing.Dict[str, typing.Any]:
        """  将用户信息组装成字典
        """
        payload: typing.Dict[str, typing.Any] = {
            "user_id": self.id,
            "identifier": self.identifier,
            "email": self.email or "",
            "create_at": self.create_at,
        }
        return payload

    @staticmethod
    def transform_password(password: str) -> str:
        from passlib.hash import hex_md5
        new_password: str = hex_md5.hash(password)
        return new_password

    @login_manager.user_loader
    def user_loader(uid: int) -> typing.Optional["User"]:
        print(f" user_loader callback: {uid}")
        user: typing.Optional['User'] = User.query.filter_by(id=uid).first()
        return user


class Conversation(db.Model):
    """
    会话

    """
    __tablename__ = "conversation"

    cov_id = Column(
        db.Integer,
        Sequence("conv_id_seq", start=1, increment=1),
        primary_key=True
    )
    identifier = Column(
        db.String(32),
        nullable=False,
        unique=True,
        comment="会话的标识符，在某些情况不适合用id，会用此字段"
    )
    user_id = Column(db.Integer, nullable=False, comment="用户")
    chats = db.relationship(
        "ChatRecord", backref="chat_record.conversation", lazy="dynamic"
    )
    create_at = Column(db.Integer, nullable=False, comment="创建时间")

    def __init__(
        self, user: User, identifier: typing.Optional[str] = None
    ) -> None:
        self.user_id = user.id
        self.identifier = identifier or uuid4().hex
        self.create_at = get_unix_time_tuple(millisecond=True)

    @staticmethod
    def get_conversation_by_identifier(
        identifier: str
    ) -> typing.Optional["Conversation"]:
        conversation: typing.Optional[Conversation
                                     ] = Conversation.query.filter_by(
                                         identifier=identifier
                                     ).first()
        return conversation


class ChatRecord(db.Model):
    """ 聊天记录
    """
    __tablename__ = "chat_record"

    chat_id = Column(
        db.Integer,
        Sequence("chat_id_seq", start=1, increment=1),
        primary_key=True
    )
    user_id = Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    conversation = Column(
        db.Integer, db.ForeignKey("conversation.cov_id"), nullable=False
    )
    content = Column(db.Text, nullable=False, comment="聊天内容")
    role = Column(SMALLINT, nullable=False, comment="角色，0表示用户，1表示机器人")
    create_at = Column(db.Integer, nullable=False, comment="创建时间")

    def __init__(
        self,
        user: User,
        content: str,
        conversation: Conversation,
        response_chat: typing.
        Optional['ChatRecord'] = None    # 没有这个参数表示用户发起的聊天，有这个参数表示机器人回复的聊天
    ) -> None:
        self.user_id = user.id
        self.content = content
        self.conversation = conversation.cov_id
        self.create_at = get_unix_time_tuple(millisecond=True)
        self.role = 0 if response_chat else 1

    @staticmethod
    def get_records_by_user_before_time(
        user_id: int, page: int, limit: int
    ) -> typing.List['ChatRecord']:
        records: typing.List[ChatRecord] = ChatRecord.query.filter_by(
            user_id=user_id
        ).order_by(ChatRecord.create_at.desc()).offset(page * limit
                                                      ).limit(limit).all()
        return records

    @staticmethod
    def get_user_records_in_time(user_id: int, start_time: int,
                                 end_time: int) -> typing.List['ChatRecord']:
        records: typing.List[ChatRecord] = ChatRecord.query.filter_by(
            user_id=user_id
        ).filter(
            ChatRecord.create_at >= start_time,
            ChatRecord.create_at <= end_time
        ).order_by(ChatRecord.create_at.desc()).all()
        return records

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


class ChatGPTKey(db.Model):
    """ 聊天GPT的key
    """

    __tablename__ = "chat_gpt_key"

    chatkey_id = Column(
        db.Integer,
        Sequence("key_id_seq", start=1, increment=1),
        primary_key=True
    )
    user_id = Column(db.Integer, nullable=False, comment="用户")
    content = Column(db.String(256), nullable=False, comment="Key")

    is_live = Column(db.Boolean, nullable=False, comment="是否可用 0表示不可用，1表示可用")

    occupy_uid = Column(db.Integer, nullable=True, comment="占用者")

    def __init__(
        self,
        user_id: int,
        app_key: str,
        is_live: bool = True,
        occupy_uid: typing.Optional[int] = None
    ) -> None:
        self.user_id = user_id
        self.content = app_key
        self.is_live = is_live
        self.occupy_uid = occupy_uid

    @staticmethod
    def get_avaliable_key() -> typing.Optional['ChatGPTKey']:
        '''
        获取可用的key
        '''
        k: typing.Optional[ChatGPTKey] = ChatGPTKey.query.filter_by(
            is_live=True, occupy_uid=None
        ).first()
        return k

    @staticmethod
    def get_user_key_if_could(user: User) -> typing.Optional['ChatGPTKey']:
        '''
        获取用户的key
        '''
        k: typing.Optional[ChatGPTKey] = ChatGPTKey.query.filter_by(
            user_id=user.id, is_live=True
        ).first()
        return k

    def get_test_key(user: User) -> 'ChatGPTKey':
        '''
        获取测试key
        '''
        k: typing.Optional[ChatGPTKey] = ChatGPTKey(
            user_id=user.id, app_key="test_key", is_live=True, occupy_uid=None
        )
        return k
