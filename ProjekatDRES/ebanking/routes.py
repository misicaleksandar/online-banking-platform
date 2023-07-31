import requests
from ebanking import app, db
from flask import render_template, redirect, url_for, flash, request
from ebanking.forms import Register, Login, Settings, Verify, Deposit, TransactionForm, ExchangeForm
from ebanking.models import Account, Card, Transaction, Balance
from flask_login import login_user, logout_user, current_user
from multiprocessing import Queue, Process
from time import sleep
from threading import Thread


@app.route('/')
@app.route('/home')
def home_page():
    balances = []
    if current_user.is_authenticated:
        balances = Balance.query.filter_by(account=current_user.id)
    return render_template('home.html', balances=balances)


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = Register()
    if form.validate_on_submit():
        account_to_create = Account(name=form.name.data,
                                    lastname=form.lastname.data,
                                    address=form.address.data,
                                    city=form.city.data,
                                    country=form.country.data,
                                    phone_number=form.phone_number.data,
                                    email=form.email.data,
                                    password=form.password.data)
        db.session.add(account_to_create)
        db.session.commit()
        created_account = Account.query.filter_by(email=form.email.data).first()
        balance = Balance(currency='RSD', amount=0, account=created_account.id)
        db.session.add(balance)
        db.session.commit()
        return redirect(url_for('login_page'))
    if form.errors != {}:
        for error_msg in form.errors.values():
            flash(f'There was an error with creating a account: {error_msg}', category='danger')

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = Login()
    if form.validate_on_submit():
        account = Account.query.filter_by(email=form.email.data).first()
        if account and account.password == form.password.data:
            login_user(account)
            flash(f'You are logged in as: {account.email}', category='success')
            return redirect(url_for('home_page'))
        else:
            flash('Wrong email or password', category='danger')

    return render_template('login.html', form=form)


@app.route('/logout')
def logout_page():
    logout_user()
    flash('You have been logged out', category='info')
    return redirect(url_for('home_page'))


@app.route('/settings', methods=['GET', 'POST'])
def account_settings_page():
    form = Settings()
    current = current_user
    if form.validate_on_submit():
        account = Account.query.filter_by(email=form.email.data).first()
        if account and account.email != current_user.email:
            flash('Account with this email already exists', category='danger')
            return redirect(url_for('account_settings_page'))
        account = Account.query.filter_by(phone_number=form.phone_number.data).first()
        if account and account.phone_number != current_user.phone_number:
            flash('Someone already using this phone number', category='danger')
            return redirect(url_for('account_settings_page'))
        current_user.name = form.name.data
        current_user.lastname = form.lastname.data
        current_user.address = form.address.data
        current_user.city = form.city.data
        current_user.country = form.country.data
        current_user.phone_number = form.phone_number.data
        current_user.email = form.email.data
        current_user.password = form.password.data
        current_user.confirm = form.confirm.data
        db.session.commit()
        flash('The data was successfully updated', category='success')
        return redirect(url_for('home_page'))

    return render_template('settings.html', form=form, current=current)


@app.route('/verify', methods=['GET', 'POST'])
def account_verify():
    form = Verify()
    currencies = requests.get(
        'https://freecurrencyapi.net/api/v2/latest?apikey=0f8a3430-73ce-11ec-84f3-a9a70f941c55&base_currency=RSD').json()
    recnik = currencies['data']
    if form.validate_on_submit():
        card = Card.query.filter_by(number=form.number.data).first()
        ids = []
        accounts = Account.query.all()
        for account in accounts:
            ids.append(account.id)
        if card and card.name == form.name.data and card.name == current_user.name and card.expiration_day == form.expiration_day.data \
                and card.security_code == int(form.security_code.data) and card.account not in ids:
            card.account = current_user.id
            card.balance -= 1/recnik['USD']
            db.session.commit()
            flash(f'You have successfully verified your account', category='success')
            return redirect(url_for('home_page'))
        else:
            flash('Verification error', category='danger')

    return render_template('verify.html', form=form)


@app.route('/deposit', methods=['GET', 'POST'])
def account_deposit():
    form = Deposit()
    account = current_user
    if form.validate_on_submit():
        if account.card[0].balance >= form.amount.data:
            account.balance[0].amount += form.amount.data
            account.card[0].balance -= form.amount.data
            db.session.commit()
            flash(f'You have successfully paid the funds from your card', category='success')
            return redirect(url_for('home_page'))
        else:
            flash('Not enough money on your card', category='danger')

    return render_template('deposit.html', form=form, card_balance=account.card[0].balance)


@app.route('/transaction', methods=['GET', 'POST'])
def new_transaction():
    form = TransactionForm()
    account = current_user
    if form.validate_on_submit():
        account = current_user
        email = account.email
        process = Process(target=transaction, args=[email, form.select.data, form.to.data, form.amount.data])
        process.start()

    return render_template('transaction.html', form=form)


def transaction(fromm, select, to, amount):
    account = Account.query.filter_by(email=fromm).first()

    transactionn = Transaction(sender=account.email, receiver=to, amount=amount, state="U OBRADI")
    db.session.add(transactionn)
    db.session.commit()

    id = transactionn.id

    sleep(120)

    if account.balance[0].amount >= amount:
        if select == '1':
            if account.email == to:
                transactionn = Transaction.query.filter_by(id=id).first()
                transactionn.state = 'ODBIJENA'
                db.session.commit()
                return

            to_account = Account.query.filter_by(email=to).first()
            if to_account:
                to_account.balance[0].amount += amount

            account.balance[0].amount -= amount
            db.session.commit()
            transactionn = Transaction.query.filter_by(id=id).first()
            transactionn.state = 'OBRADJENA'
            db.session.commit()

        elif select == '2':
            if str(account.card[0].number) == to:
                transactionn = Transaction.query.filter_by(id=id).first()
                transactionn.state = 'ODBIJENA'
                db.session.commit()
                return

            card = Card.query.filter_by(number=to).first()
            if card:
                card.balance += amount

            account.balance[0].amount -= amount
            transactionn = Transaction.query.filter_by(id=id).first()
            transactionn.state = 'OBRADJENA'
            db.session.commit()
    else:
        transactionn = Transaction.query.filter_by(id=id).first()
        transactionn.state = 'ODBIJENA'
        db.session.commit()


@app.route('/transactions')
def show_all():
    transactions = list(Transaction.query.filter_by(sender=current_user.email))

    if transactions:
        transactions1 = list(Transaction.query.filter_by(receiver=current_user.email))
        for t in transactions1:
            if t not in transactions:
                transactions.append(t)
    else:
        transactions += list(Transaction.query.filter_by(receiver=current_user.email))

    if transactions:
        transactions1 = list(Transaction.query.filter_by(receiver=current_user.card[0].number))
        for t in transactions1:
            if t not in transactions:
                transactions.append(t)
    else:
        transactions += list(Transaction.query.filter_by(receiver=current_user.card[0].number))

    return render_template('transactions.html', transactions=transactions)


@app.route('/sort', methods=['GET', 'POST'])
def sort_func():

    selection = request.form.get('selection')

    transactions = list(Transaction.query.filter_by(sender=current_user.email))

    if transactions:
        transactions1 = list(Transaction.query.filter_by(receiver=current_user.email))
        for t in transactions1:
            if t not in transactions:
                transactions.append(t)
    else:
        transactions += list(Transaction.query.filter_by(receiver=current_user.email))

    if transactions:
        transactions1 = list(Transaction.query.filter_by(receiver=current_user.card[0].number))
        for t in transactions1:
            if t not in transactions:
                transactions.append(t)
    else:
        transactions += list(Transaction.query.filter_by(receiver=current_user.card[0].number))

    if selection == 'Ascending':

        transactions.sort(reverse=False, key=lambda x: x.amount)
        return render_template('transactions.html', transactions=transactions)
    else:

        transactions.sort(reverse=True, key=lambda x: x.amount)
        return render_template('transactions.html', transactions=transactions)


@app.route('/search', methods=['GET', 'POST'])
def search_func():
    transactions = list(Transaction.query.filter_by(sender=current_user.email))

    if transactions:
        transactions1 = list(Transaction.query.filter_by(receiver=current_user.email))
        for t in transactions1:
            if t not in transactions:
                transactions.append(t)
    else:
        transactions += list(Transaction.query.filter_by(receiver=current_user.email))

    if transactions:
        transactions1 = list(Transaction.query.filter_by(receiver=current_user.card[0].number))
        for t in transactions1:
            if t not in transactions:
                transactions.append(t)
    else:
        transactions += list(Transaction.query.filter_by(receiver=current_user.card[0].number))

    sender = request.form.get("sender")
    receiver = request.form.get("receiver")
    amountOd = request.form.get("amountOd")
    amountDo = request.form.get("amountDo")

    new_transactions = []

    if amountOd == '' and amountDo == '':
        for transaction in transactions:
            if sender in transaction.sender:
                if receiver in transaction.receiver:
                    new_transactions.append(transaction)

    if amountDo == '' and amountOd != '':
        for transaction in transactions:
            if sender in transaction.sender:
                if receiver in transaction.receiver:
                    if int(amountOd) <= transaction.amount:
                        new_transactions.append(transaction)

    if amountOd == '' and amountDo != '':
        for transaction in transactions:
            if sender in transaction.sender:
                if receiver in transaction.receiver:
                    if int(amountDo) >= transaction.amount:
                        new_transactions.append(transaction)

    if amountOd != '' and amountDo != '':
        for transaction in transactions:
            if sender in transaction.sender:
                if receiver in transaction.receiver:
                    if int(amountDo) >= transaction.amount and int(amountOd) <= transaction.amount:
                        new_transactions.append(transaction)

    return render_template('transactions.html', transactions=new_transactions)


@app.route('/exchange', methods=['GET', 'POST'])
def exchange_func():
    form = ExchangeForm()
    currencies = requests.get(
        'https://freecurrencyapi.net/api/v2/latest?apikey=0f8a3430-73ce-11ec-84f3-a9a70f941c55&base_currency=RSD').json()
    recnik = currencies['data']
    list_of_currencies = []
    for key in recnik:
        list_of_currencies.append(key)

    if form.validate_on_submit():
        selection = request.form.get('selection')
        current = current_user
        q = Queue()
        thread1 = Thread(target=exchange_thread, args=[form.amount.data, selection, recnik, current.email, q])
        thread1.start()

        result = q.get()
        if result:
            flash('Successful exchange', category='success')
        else:
            flash('Not enough money', category='danger')

    return render_template('exchange.html', currencies=list_of_currencies, form=form)


def exchange_thread(amount, selection, recnik, email, q):

    current = Account.query.filter_by(email=email).first()

    if current.balance[0].amount >= amount:
        current.balance[0].amount -= amount
        new_amount = amount * recnik[selection]
        current_balance = Balance.query.filter_by(currency=selection, account=current.id).first()
        if current_balance:
            current_balance.amount += new_amount
        else:
            new_balance = Balance(currency=selection, amount=new_amount, account=current.id)
            db.session.add(new_balance)

        db.session.commit()
        q.put(True)
    else:
        q.put(False)
