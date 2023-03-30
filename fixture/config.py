# -*- coding: utf-8 -*-
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

GPT_ORGANIZATION = ""
GPT_API_KEY = ""

ADMIN_USER_IDENTIFIER = ""
ADMIN_USER_MOBILEPHONE = ""
ADMIN_USER_EMAIL = ""
ADMIN_USER_PASSWORD = ""

SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(
    CURRENT_DIR, "data.sqlite"
)

WEB_PORT = 5000
WEB_ADDRESS = "0.0.0.0"

USE_SSL = False
