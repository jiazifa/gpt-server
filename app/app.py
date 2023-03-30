# -*- coding: utf-8 -*-
import os
import typing
from flask import Flask, redirect, url_for, render_template
from flask.cli import AppGroup
from flask_admin import Admin
from flask_migrate import Migrate

from app.ext import login_manager, db

__all__ = ["create_app"]


def __config_default_config(app: Flask) -> None:
    app.config.from_mapping(
        {
    # Login Secret Key
            "SECRET_KEY": "dev",
            "FLASK_ADMIN_SWATCH": "cerulean",
            "ADMIN_USER_IDENTIFIER": "admin_identifier",
    # GPT
    # fake organization and api key
            "GPT_ORGANIZATION": "fake_organization",
            "GPT_API_KEY": "fake_api_key",
            "GPT_MODEL": "gpt-3.5-turbo",
            "GPT_MAX_TOKENS": 2048,
            "GPT_TEMPERATURE": 0.2,

    # DB
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_COMMIT_ON_TEARDOWN": False,
            "SQLALCHEMY_RECORD_QUERIES": False,
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "SQLALCHEMY_ECHO": False,
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "pool_pre_ping": True,
            },

    # Web Port & Address
            "WEB_PORT": 5000,
            "WEB_ADDRESS": "0.0.0.0"
        }
    )
    try:
        for p in [app.instance_path]:
            if not os.path.exists(p):
                os.makedirs(p)
    except OSError:
        pass


def __config_database(app: Flask) -> None:
    # db
    db.init_app(app=app)
    migrate = Migrate(app, db, command="db")

    db_cli = AppGroup("database", help="Database commands. (db)")

    @db_cli.command("init")
    def init_db():
        with app.app_context():
            db.create_all()

    @db_cli.command("create")
    def create():
        from sqlalchemy_utils.functions import database_exists, create_database
        db_url: str = app.config["SQLALCHEMY_DATABASE_URI"]
        print(f"create database: {db_url}")
        if not database_exists(db_url):
            create_database(db_url)

    app.cli.add_command(db_cli)


def __setup_admin(app: Flask) -> None:
    # admin
    from flask import redirect, url_for, current_app
    from flask_admin import AdminIndexView
    from flask_admin.contrib.sqla import ModelView
    from app.model import User, ChatGPTKey

    class AuthAdminIndexView(AdminIndexView):

        def is_accessible(self):
            from flask_login import current_user
            return current_user.is_authenticated and current_user.identifier == current_app.config[
                "ADMIN_USER_IDENTIFIER"]

        def inaccessible_callback(self, name, **kwargs):
            return redirect(url_for("auth.admin_login"))

    class AuthModelView(ModelView):

        def is_accessible(self):
            from flask_login import current_user
            return current_user.is_authenticated and current_user.identifier == current_app.config[
                "ADMIN_USER_IDENTIFIER"]

        def inaccessible_callback(self, name, **kwargs):
            return redirect(url_for("auth.admin_login"))

    admin = Admin(
        app,
        name="ChatGPT用户管理",
        template_mode="bootstrap3",
        index_view=AuthAdminIndexView()
    )

    admin.add_view(AuthModelView(User, db.session))
    admin.add_view(AuthModelView(ChatGPTKey, db.session))


def __setup_blueprint(app: Flask) -> None:
    # blueprint
    from app import gpt
    from app import auth

    gpt.init_app(app=app)
    app.register_blueprint(gpt.bp)
    app.register_blueprint(auth.bp)
    # login
    login_manager.init_app(app=app)

    @app.get("/admin/")
    def admin_index():
        return redirect(url_for("admin.index"))

    app.url_map.strict_slashes = False

    def create_admin_user_if_needed():
        from app.model import User
        with app.app_context():
            from sqlalchemy import inspect
            insp = inspect(db.engine)
            tables = insp.get_table_names(schema="main")
            if "user" not in tables:
                print("user table not exists")
                return

            admin_identifier = app.config["ADMIN_USER_IDENTIFIER"]
            admin = User.query.filter_by(identifier=admin_identifier).all()
            if admin:
                print(f"admin user already exists {admin}")
                return
            name = "admin"
            email = app.config["ADMIN_USER_EMAIL"]
            password = app.config["ADMIN_USER_PASSWORD"]
            new_password = User.transform_password(password)
            print(f"will create user {name} with password {password}")
            admin = User(email=email, password=new_password)
            admin.identifier = admin_identifier
            db.session.add(admin)
            db.session.commit()

    create_admin_user_if_needed()


def __setup_login_manager(app: Flask) -> None:
    # login
    from flask import Request
    from app.model import User

    @login_manager.unauthorized_handler
    def register_unauthorized():
        print(f"unauthorized")
        return {"code": 401, "msg": "认证错误, 请重新登录", "data": None}

    @login_manager.request_loader
    def load_user_from_request(request: Request) -> typing.Optional['User']:
        # first, try to login using the api_key url arg
        from app.model import User

        # next, try to login using Basic Auth
        api_key = request.headers.get('Authorization')
        if not api_key:
            print(f"no api key found")
            return None
        token = api_key.replace('Token ', '', 1).strip()

        user: typing.Optional['User'] = User.query.filter_by(token=token
                                                            ).first()
        if not user:
            print(f"token {token} not found")
            return None
        print(f"token {token} found: {user}")
        return user


def create_app(
    test_config: typing.Optional[typing.Dict[str, typing.Any]] = None
) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    __config_default_config(app=app)

    app.config.from_pyfile("config.py", silent=False)
    if test_config:
        app.config.from_mapping(test_config)

    __config_database(app=app)
    __setup_admin(app=app)
    __setup_blueprint(app=app)
    __setup_login_manager(app=app)
    return app
