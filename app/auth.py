# -*- coding: utf-8 -*-
import typing
import datetime
from flask import request, Blueprint, redirect, url_for, render_template, g
from app.ext import login_manager, db
from app.utils import get_random_num, parse_params
from flask_login import login_required, login_user, logout_user, current_user
from app.model import User
from app.response import response_succ, response_error

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/logout/", methods=["GET", "POST"])
def logout():
    """登出接口

    """
    logout_user()
    print(f"server logout info: {current_user}")
    return response_succ(body={"content": "Your logout"})


@bp.route("/uid/", methods=["GET", "POST"])
def uid():
    return response_succ(
        body={
            "uid": get_random_num(6),
            'method': request.method
        }
    )


@bp.route("/login/", methods=["POST"])
def login():
    """登录接口
    """
    params = parse_params(request)
    email = params.get("email")
    if not email:
        return response_error(error_code=400, msg='邮箱不能为空')
    password = params.get("password")
    if not password:
        return response_error(error_code=400, msg="密码不能为空")

    query_options = [User.email == email]
    if password:
        new_password = User.transform_password(password)
        query_options.append(User.password == new_password)

    u: typing.Optional[User] = User.query.filter(*query_options).first()
    if not u:
        return response_error(error_code=400, msg="用户名或密码错误")
        # update token
    new_token: str = User.transform_password(f"{email}{get_random_num(6)}")
    u.token = new_token
    info: typing.Dict[str, typing.Any] = u.to_json()
    info.setdefault("token", new_token)
    print(f"server login info: {info}")
    login_user(u, remember=True, duration=datetime.timedelta(days=15))
    db.session.add(u)
    db.session.commit()
    return response_succ(body=info)


@bp.route("/info/", methods=["GET"])
@login_required
def info():
    """用户信息接口

    """
    user: User = current_user
    return response_succ(body=user.to_json())


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
