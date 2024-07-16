from flask import render_template, flash, redirect, url_for, request, session
from sqlalchemy import or_

from app import app, bcrypt, db
from app.decorators import login_required
from app.forms import RegistrationForm, LoginForm, AddBalance, TransferMoney, TransferHistoryForm, DeleteForm, \
    SupportTeam, ForgotPassword, VerifyCodeForm
from random import randint
from app.models import User, Balance, TransferHistory, Complains
from app.utils import save_image
from app.email import send_notification_code


@app.route('/')
def home():
    return render_template('index.html', title='HomePage')


@app.route('/register', methods=['GET', 'POST'])
@login_required(required=False)
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        try:
            hashed_pass = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            image = None
            if form.image.data:
                image = save_image(form.image.data)

            user = User(fullname=form.fullname.data, username=form.username.data,
                        email=form.email.data, password=hashed_pass, image_url=image,
                        date_birth=form.birth_date.data,
                        sex=form.sex.data)
            db.session.add(user)
            db.session.commit()
            flash("You successfully registered", 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Exseption occured {e}')
    return render_template('auth/register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
@login_required(required=False)
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if not user.is_deleted or not user.is_active:
            if user and bcrypt.check_password_hash(user.password, form.password.data):
                session['user_id'] = user.id
                session['username'] = user.username
                session['fullname'] = user.fullname
                flash(f"Welcome {user.fullname}", 'success')
                return redirect(url_for('home'))
            else:
                user.failure_attempts += 1
                if user.failure_attempts >= 3:
                    user.locker()
                    flash('You blocked due many attempts! To recover account contact with support!', 'danger')
                    return redirect(url_for('support_team'))
                else:
                    flash('username or password is wrong', category='danger')
                    db.session.commit()
        else:
            flash('This user deleted or inactive! To recover account contact with support!', category='danger')

    return render_template('auth/login.html', form=form)


@app.route('/forgot-password', methods=['GET', 'POST'])
@login_required(required=False)
def forgot_password():
    form = ForgotPassword()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data, email=form.email.data).first()
        if user:
            code = randint(100000, 999999)
            session['code'] = code
            session['user_id'] = user.id
            try:
                send_notification_code(code, form.email.data)
                flash('A verification code has been sent to your email.', 'info')
            except Exception as e:
                flash('Failed to send email. Please try again later.', 'danger')
                return redirect(url_for('forgot_password'))

            return redirect(url_for('verify_code'))
        else:
            flash('User not found!', 'danger')

    return render_template('forgot-password.html', form=form)


@app.route('/verify-code', methods=['GET', 'POST'])
def verify_code():
    form = VerifyCodeForm()
    if form.validate_on_submit():
        user_id = session.get('user_id')
        code = session.get('code')
        if user_id and code:
            user = User.query.filter_by(id=user_id).first()
            if user and code == int(form.code.data):
                user.password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
                db.session.commit()
                flash('Password has been successfully changed', 'success')
                session.pop('code', None)
                session.pop('user_id', None)
                return redirect(url_for('login'))
            else:
                flash('Invalid code!', 'danger')
        else:
            flash('Session expired. Please try again.', 'danger')
            return redirect(url_for('forgot_password'))

    return render_template('verify-code.html', form=form)


@app.route('/logout')
@login_required(required=True)
def logout():
    try:
        session.pop('user_id')
        session.pop('username')
        session.pop('fullname')
        flash('You successfully logged out', 'success')
        return render_template('index.html', title='HomePage')
    except KeyError:
        return redirect(url_for('home'))


@app.route('/add-balance', methods=['POST', 'GET'])
@login_required(required=True)
def add_balance():
    user_id = session.get('user_id')
    form = AddBalance()
    if form.validate_on_submit():
        amount = form.amount.data
        user = User.query.filter_by(id=user_id).first()
        user_balance = Balance.query.filter_by(user_id=user.id).first()
        if user_balance:
            user_balance.amount += float(amount)
        else:
            balance = Balance(amount=float(amount), user_id=user.id)
            db.session.add(balance)
        db.session.commit()
        flash('Add balance successfully', 'success')
        return redirect(url_for('home'))
    return render_template('add_balance.html', form=form)


@app.route('/show-balance')
@login_required(required=True)
def show_balance():
    user_id = session.get('user_id')
    balance = Balance.query.filter_by(user_id=user_id).first()
    return render_template('show-balance.html', balance=balance)


@app.route('/transfer-money', methods=['GET', 'POST'])
@login_required(required=True)
def transfer_money():
    form = TransferMoney()
    if form.validate_on_submit():
        user_id = session.get('user_id')
        money = form.amount.data
        receiver_id = form.receiver.data
        description = form.description.data

        sender = User.query.get(user_id)
        receiver = User.query.get(receiver_id)

        if not receiver:
            flash('Receiver not found', 'danger')
            return redirect(url_for('transfer_money'))
        if receiver_id == user_id:
            flash('You can not transfer in self', 'danger')
            return redirect(url_for('transfer_money'))
        if sender.id != user_id:
            session.pop('user_id')

        sender_balance = Balance.query.filter_by(user_id=user_id).first()
        receiver_balance = Balance.query.filter_by(user_id=receiver_id).first()

        if sender_balance.amount < money:
            flash('You do not have enough money for transfer', 'danger')
            return redirect(url_for('transfer_money'))

        try:
            sender_balance.amount -= money

            if receiver_balance:
                receiver_balance.amount += money
            else:
                new_receiver_balance = Balance(amount=money, user_id=receiver_id)
                db.session.add(new_receiver_balance)

            transfer_history = TransferHistory(
                amount=money, sender_id=user_id, receiver_id=receiver_id, description=description)
            db.session.add(transfer_history)

            db.session.commit()

            flash('Money transferred successfully', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during the transfer', 'danger')
            return redirect(url_for('transfer_money'))

    return render_template('transfer_money.html', form=form)


@app.route('/transfer-history', methods=['GET', 'POST'])
@login_required(required=True)
def transfer_history():
    form = TransferHistoryForm()
    user_id = session.get('user_id')

    history = TransferHistory.query.filter(
        or_(TransferHistory.sender_id == user_id, TransferHistory.receiver_id == user_id),
    ).all()
    message = None

    if form.validate_on_submit():
        start_date = form.start_period.data
        end_date = form.end_period.data

        if start_date and end_date:
            if start_date < end_date:
                history = TransferHistory.query.filter(
                    or_(TransferHistory.sender_id == user_id, TransferHistory.receiver_id == user_id),
                    TransferHistory.timestamp >= start_date,
                    TransferHistory.timestamp <= end_date
                ).all()
            else:
                message = "End date must be after start date."
        else:
            message = "Both start date and end date are required."

    return render_template('transfer_history.html', history=history, form=form, message=message)


@app.route('/delete', methods=['GET', 'POST'])
def delete():
    form = DeleteForm()
    if form.validate_on_submit():
        user = User.query.filter_by(id=session.get('user_id'), username=form.username.data,
                                    email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            user.is_deleted = True
            db.session.commit()
            user_id = session.pop('user_id')
            session.pop('username')
            session.pop('fullname')
            flash('You deleted account.But you can recover the account again.', 'info')
            return render_template('index.html', title='HomePage')
        else:
            flash('username or password is wrong!', 'danger')
    return render_template('delete_account.html', form=form)


@app.route('/profile')
def profile():
    user = User.query.filter_by(id=session.get('user_id')).first()
    if user.image_url:
        image = user.image_url
    else:
        if user.sex == 'male':
            image = 'static/images/depositphotos_171453724-stock-illustration-default-avatar-profile-icon-grey_man.webp'
        else:
            image = 'static/images/depositphotos_133352152-stock-illustration-default-placeholder-profile-icon_woman.webp'
    return render_template('profile.html', user=user, image=image)


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    user_id = session.get('user_id')
    user = User.query.filter_by(id=user_id).first()
    form = RegistrationForm(obj=user)
    if form.validate_on_submit():
        form.populate_obj(obj=user)
        if form.image.data:
            image_path = save_image(form.image.data)
            user.image_url = image_path
        db.session.commit()
        flash('Profile successfully edited', 'success')
        return redirect(url_for('register'))
    return render_template('edit.html', form=form, user=user)


@app.route('/support-team', methods=['GET', 'POST'])
def support_team():
    form = SupportTeam()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        complain = Complains(username=form.username.data, text=form.text.data)
        db.session.add(complain)
        db.session.commit()
        user.reset_activate()
        return redirect(url_for('login'))
    return render_template('support-team.html', form=form)
