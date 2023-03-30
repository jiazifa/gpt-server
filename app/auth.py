# -*- coding: utf-8 -*-
import typing
import datetime
from flask import request, Blueprint, redirect, url_for, render_template, g
from app.ext import login_manager, db
from app.utils import get_random_num, parse_params
from flask_login import login_required, login_user, current_user
from app.model import User

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login/", methods=["POST"])
def login():
    params = parse_params(request)
    email = params.get("email")
    if not email:
        return {"code": 400, "msg": "邮箱不能为空"}
    password = params.get("password")
    if not password:
        return {"code": 400, "msg": "密码不能为空"}

    query_options = [User.email == email]
    if password:
        new_password = User.transform_password(password)
        query_options.append(User.password == new_password)

    u: typing.Optional[User] = User.query.filter(*query_options).first()
    if not u:
        return {"code": 400, "msg": "用户名或密码错误"}
        # update token
    new_token: str = User.transform_password(f"{email}{get_random_num(6)}")
    u.token = new_token
    info: typing.Dict[str, typing.Any] = u.to_json()
    info.setdefault("token", new_token)
    print(f"server login info: {info}")
    login_user(u, remember=True, duration=datetime.timedelta(days=15))
    db.session.add(u)
    db.session.commit()
    return {"code": 200, "msg": "登录成功", "data": info}


@bp.route("/info/", methods=["GET"])
@login_required
def info():
    """用户信息接口

    """
    user: User = current_user
    return {"code": 200, "msg": "获取成功", "data": user.to_json()}


@bp.route('/admin_login/', methods=['GET'])
def admin_login():
    return render_template('login.html')


@bp.route('/admin_login_form/', methods=['POST'])
def admin_login_form():
    email = request.form['email']
    password = request.form['password']
    new_password = User.transform_password(password)
    u: typing.Optional[User] = User.query.filter_by(
        email=email, password=new_password
    ).first()
    if not u:
        return redirect(url_for('auth.admin_login'))
    login_user(u, remember=True, duration=datetime.timedelta(days=15))

    return redirect(url_for('admin.index'))
