# -*- coding: utf-8 -*-
import typing
import pytest
from flask.testing import FlaskClient
from app import create_app


def test_config():
    assert not create_app().testing
    assert create_app({'TESTING': True}).testing


@pytest.fixture
def client() -> FlaskClient:
    app = create_app(
        {
            'TESTING': True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )
    from app.model import User
    from app.ext import db
    with app.app_context():
        # create test user
        db.create_all()
        if not User.get_user_by_email("test@email.com"):
            user = User(
                email="test@email.com",
                password=User.transform_password("admin")
            )
            db.session.add(user)
            db.session.commit()
        if not User.get_user_by_email("test@email.com"):
            user = User(email="test_02@email.com", password=None)
            db.session.add(user)
            db.session.commit()

    with app.test_client() as client:
        yield client


@pytest.fixture
def login_in_token(client: FlaskClient) -> typing.Optional[str]:
    from app.model import User
    response = client.post(
        '/auth/login/', json={
            "email": "test@email.com",
            "password": "admin"
        }
    )
    token: typing.Optional[str] = response.json["data"]["token"]
    return token


def test_auth_login_no_password(client: FlaskClient):
    response = client.post('/auth/login/', json={
        "email": "test@email.com",
    })
    assert response.json["code"] == 400


def test_auth_login(client: FlaskClient):
    response = client.post(
        '/auth/login/', json={
            "email": "test@email.com",
            "password": "admin"
        }
    )
    assert response.json["code"] == 200
    assert response.json["data"]["token"] is not None
    assert response.status_code == 200


def test_auth_info(client: FlaskClient, login_in_token: str):
    response = client.get(
        '/auth/info/', headers={'Authorization': f"Token {login_in_token}"}
    )
    assert response.json["code"] == 200
    assert response.json["data"]["user_id"]
    assert response.json["data"]["email"] == "test@email.com"


def test_gpt(client: FlaskClient, login_in_token: str):
    response = client.post(
        '/gpt/competion/',
        headers={'Authorization': f"Token {login_in_token}"},
        json={'messages': [{
            "role": "user",
            "content": "你好"
        }]},
    )
    print(f"response: {response.json}")
    content: str = response.json["data"]
    assert len(content) > 0


def test_gpt_no_prompt(client: FlaskClient, login_in_token: str):
    response = client.post(
        '/gpt/competion/',
        headers={'Authorization': f"Token {login_in_token}"},
        json={'messages': [{
            "role": "user",
            "content": ""
        }]}
    )
    assert response.json["code"] == 400
    assert response.status_code == 200


@pytest.mark.parametrize(("prompt"), ("你好", "hello", "こんにちは"))
def test_gpt_async(client: FlaskClient, login_in_token: str, prompt: str):
    response = client.post(
        '/gpt/competion/',
        headers={'Authorization': f"Token {login_in_token}"},
        json={'messages': [{
            "role": "user",
            "content": prompt
        }]}
    )
    print(f"response: {response.json}")
    content: str = response.json["data"]
    assert len(content) > 0


def test_chat_records(client: FlaskClient, login_in_token: str):
    client.post(
        '/gpt/competion/',
        headers={'Authorization': f"Token {login_in_token}"},
        json={'messages': [{
            "role": "user",
            "content": "hello"
        }]}
    )
    response = client.post(
        '/gpt/chat_records/',
        headers={'Authorization': f"Token {login_in_token}"},
        json={
            'limit': 10,
            'page': 0
        }
    )
    content = response.json["data"]
    print(f"content: {content}")
    assert content[0]["content"] == "hello"
    assert content[0]["create_at"] <= content[1]["create_at"]
    assert content[0]["role"] == 1
    assert content[1]["role"] == 0
    assert len(content) == 2


@pytest.mark.parametrize(("prompt"), ("你好", "hello", "こんにちは"))
def test_gpt_chat(client: FlaskClient, login_in_token: str, prompt: str):
    response = client.post(
        '/gpt/competion/',
        headers={'Authorization': f"Token {login_in_token}"},
        json={'messages': [{
            "role": "user",
            "content": prompt
        }]}
    )
    content: str = response.json["data"]
    assert len(content) > 0


def test_gpt_chat_prompt(client: FlaskClient, login_in_token: str):
    prompt = "test"
    response = client.post(
        '/gpt/competion/',
        headers={'Authorization': f"Token {login_in_token}"},
        json={'messages': [{
            "role": "user",
            "content": prompt
        }]}
    )
    content: str = response.json["data"]
    assert len(content) > 0


def test_gpt_chat_prompt_multy(client: FlaskClient, login_in_token: str):
    prompt = "test_random_1"
    response = client.post(
        '/gpt/competion/',
        headers={'Authorization': f"Token {login_in_token}"},
        json={'messages': [{
            "role": "user",
            "content": prompt
        }]}
    )

    prompt = "test_random_2"
    response = client.post(
        '/gpt/competion/',
        headers={'Authorization': f"Token {login_in_token}"},
        json={'messages': [{
            "role": "user",
            "content": prompt
        }]}
    )
    print(f"response: {response.json}")
    content = response.json["data"]
    assert len(content) > 2
