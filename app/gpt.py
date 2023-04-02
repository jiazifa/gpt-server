# -*- coding: utf-8 -*-
import os
import typing
from random import choice
from openai import ChatCompletion
from flask import Flask, Blueprint, current_app, request
from flask_login import login_required, current_user
import openai
from app.ext import db
from app.utils import parse_params
from app.response import response_error, response_succ
from app.model import ChatRecord, User, Conversation, ChatGPTKey

bp = Blueprint("gpt", __name__, url_prefix="/gpt")


def __get_default_params_from_params(params: typing.Dict[str, typing.Any]):
    model: str = params.get("model") or current_app.config["GPT_MODEL"]
    max_token = int(
        params.get("max_token") or current_app.config["GPT_MAX_TOKENS"]
    )
    temperature = float(
        params.get("temperature") or current_app.config["GPT_TEMPERATURE"]
    )
    return model, max_token, temperature


@bp.route("/competion/", methods=["POST"])
@login_required
def create_competion():
    user: User = current_user
    params = parse_params(request)
    messages: typing.List[typing.Dict[str, str]] = params.get("messages") or []
    conversation_idf = params.get("conversation")

    model, max_token, temperature = __get_default_params_from_params(params)

    if not messages or len(messages) == 0:
        return response_error(error_code=400, msg="messages is empty")
    last_message = messages[-1]
    last_prompt = last_message.get("content")
    if not last_prompt:
        return response_error(error_code=400, msg="prompt is empty")

    print(f"询问内容: {last_prompt}")

    conversation = Conversation.get_conversation_by_identifier(
        conversation_idf
    )
    if not conversation:
        conversation = Conversation(user=user, identifier=conversation_idf)
        db.session.add(conversation)

    api_key: typing.Optional[ChatGPTKey] = None

    if current_app.config["TESTING"]:
        # fill test api key
        api_key = ChatGPTKey.get_test_key(user=user)

    if user_key := ChatGPTKey.get_user_key_if_could(user):
        api_key = user_key

    if not api_key:
        keys = ChatGPTKey.get_avaliable_key()
        k: ChatGPTKey = choice(keys)
        if k:
            api_key = k.content

    if not api_key:
        return response_error(error_code=400, msg="当前服务繁忙，请稍后再试")

    prompt_record = ChatRecord(
        user=user,
        content=last_prompt,
        conversation=conversation,
        response_chat=None
    )
    api_key.occupy_uid = user.id
    db.session.add(prompt_record)
    db.session.commit()
    try:
        content_striped: str
        if current_app.config["TESTING"]:
            content_striped = f"测试内容: 我是{last_prompt}问题的回答"
        else:
            resp = ChatCompletion.create(
                api_key=api_key,
                model=model,
                messages=messages,
                max_tokens=max_token,
                temperature=temperature,
                timeout=10,
            )

            choices = resp["choices"]
            if not choices or len(choices) == 0:
                return response_error(error_code=400, msg="当前服务繁忙，请稍后再试")
            print(f"回答内容: choices: {choices}")
            first_choices: dict = choices[0]
            message: dict = first_choices["message"]
            content: str = message["content"]
            content_striped = content.strip()

        resp_record = ChatRecord(
            user=user,
            content=content_striped,
            conversation=conversation,
            response_chat=prompt_record
        )
        db.session.add(resp_record)
        db.session.commit()
        return response_succ(body=content_striped)
    except openai.error.RateLimitError as e:
        print(f"RateLimitError: {e}")
        return response_error(error_code=400, msg="当前服务繁忙，请稍后再试")
    except Exception as e:
        print(f"exception: {e}")
        return response_error(error_code=400, msg="请稍后再试")
    finally:
        api_key.occupy_uid = None
        db.session.commit()


@bp.route("/chat_records/", methods=["POST"])
@login_required
def get_recent_chat_records():
    user: User = current_user
    params = parse_params(request)
    limit: int = params.get("limit", 10)
    page: int = params.get("page", 0)
    records = ChatRecord.get_records_by_user_before_time(
        user_id=user.id, limit=limit, page=page
    )
    return response_succ(body=[record.to_json() for record in records])


def init_app(app: Flask):
    ...
