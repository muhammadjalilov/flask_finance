from functools import wraps

from flask import session, flash, redirect, url_for

from app.models import User


def login_required(required=True):
    def decorator_func(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_id = session.get('user_id')
            user = User.query.filter_by(id=user_id).first()
            if required and not session.get('user_id'):
                flash('You should first log in!', 'danger')
                return redirect(url_for('login'))
            if not required and session.get('user_id'):
                flash('You are already registered!', 'info')
                return redirect(url_for('home'))
            if not user and required:
                session.pop('user_id')
            return func(*args, **kwargs)

        return wrapper

    return decorator_func
