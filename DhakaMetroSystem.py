from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)

app.config['SECRET_KEY']='dsfcsdvsdv'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://dms:abcd1234@localhost:3306/dms'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#DB model

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(30), nullable=False, unique=True)
    email = db.Column(db.Text, nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)
    Fname = db.Column(db.String(30))
    Lname = db.Column(db.String(30))
    phone = db.Column(db.String(30))
    address = db.Column(db.String(30))
    aType = db.Column(db.String(30), nullable=False, default='Regular User')
    aStatus = db.Column(db.String(30), default='Unbanned')

    def __repr__(self):
        return f'User {self.username}'
    
class PassCard(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    card_no = db.Column(db.Integer, nullable=False, unique=True)
    card_type = db.Column(db.String(30), nullable=False)
    card_balance = db.Column(db.Integer, nullable=False)
    card_view = db.Column(db.Integer, nullable=False, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('passcards', lazy=True))

    def __repr__(self):
        return f'PassCard {self.card_no}'
    
class Recharge(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    wallet_type = db.Column(db.String(30), nullable=False)
    card_no = db.Column(db.Integer, nullable=False)
    wallet_mobile = db.Column(db.String(30), nullable=False)
    trxid = db.Column(db.String(30), nullable=False)
    recharge_amount = db.Column(db.Integer, nullable=False)
    recharge_date = db.Column(db.DateTime(timezone=True), default=func.now())
    card_id = db.Column(db.Integer, db.ForeignKey('pass_card.id'), nullable=False)
    card = db.relationship('PassCard', backref=db.backref('recharges', lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('recharges', lazy=True))
    status = db.Column(db.String(30), nullable=False, default='Pending')

    
    def __repr__(self):
        return f'Recharge {self.recharge_amount}'

class Station(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    station_name = db.Column(db.String(30), nullable=False)
    station_serial = db.Column(db.Integer, nullable=False)


    def __repr__(self):
        return f'Station {self.station_name}'

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    trip_date = db.Column(db.String(30), nullable=False)
    start = db.Column(db.String(30), nullable=False)
    dest = db.Column(db.String(30), nullable=False)
    trip_fare = db.Column(db.Integer, nullable=False)
    trip_card = db.Column(db.Integer, nullable=False)
    trip_user = db.Column(db.Integer, nullable=False)
    trip_status = db.Column(db.String(30), nullable=False, default='Pending')
    payment_status = db.Column(db.String(30), nullable=False, default='Unpaid')
    trip_time = db.Column(db.String(30))

    def __repr__(self):
        return f'Trip {self.id}'
    
class voucher(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    voucher_code = db.Column(db.String(30), nullable=False)
    voucher_amount = db.Column(db.Integer, nullable=False)
    voucher_status = db.Column(db.String(30), nullable=False, default='Eligible')
    voucher_admin=db.Column(db.String(30))

    def __repr__(self):
        return f'Voucher {self.id}'

class refund(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    refund_amount = db.Column(db.Integer, nullable=False)
    refund_date = db.Column(db.DateTime(timezone=True), default=func.now())
    refund_status = db.Column(db.String(30), nullable=False, default='Pending')
    trip_user = db.Column(db.String(30), nullable=False)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'), nullable=False)
    trip = db.relationship('Trip', backref=db.backref('refunds', lazy=True))

    def __repr__(self):
        return f'Refund {self.id}'

class Complains(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    complain = db.Column(db.Text, nullable=False)
    reply = db.Column(db.Text, default='No reply yet')
    status = db.Column(db.String(30), nullable=False, default='Pending')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('complains', lazy=True))

    def __repr__(self):
        return f'Complain {self.id}'


login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user):
    return User.query.get(int(user))



#Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('useremail')
        username = request.form.get('username')
        password = request.form.get('userpassword')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        else:
            new_user = User(email=email, username=username, password=generate_password_hash(password, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        
    return render_template("signup.html", user=current_user)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('useremail')
        password = request.form.get('userpassword')

        user = User.query.filter_by(email=email).first()
        if user:
            if user.aStatus == 'Banned':
                return render_template("AccountBanned.html", user=current_user)

            if check_password_hash(user.password, password):
                login_user(user)
                if user.Fname==None or user.Lname==None or user.phone==None or  user.address==None:
                    return redirect(url_for('setup'))
                return redirect(url_for('index'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')
    return render_template("signin.html", user=current_user)

@app.route("/setup", methods=['GET', 'POST'])
@login_required
def setup():
    user=current_user
    if request.method == 'POST':
        user.Fname = request.form.get('Fname')
        user.Lname = request.form.get('Lname')
        user.phone = request.form.get('phone')
        user.address = request.form.get('address')

        db.session.commit()
        return redirect(url_for('index'))
    return render_template("setup.html", user=current_user)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/profile")
@login_required
def profile():
    
    return render_template("profile.html", user=current_user)

@app.route("/passcardRegister", methods=['GET', 'POST'])
@login_required
def passcardRegister():
    user=current_user
    flag = PassCard.query.filter_by(user_id=user.id).first()
    if flag:
        pass
    else:
        if request.method == 'POST':
            card_no = 100000 + user.id
            card_t = request.form.get('card_type')
            card_balance = 0
            new_card = PassCard(card_no=card_no, card_type=card_t, card_balance=card_balance, user_id=user.id)
            db.session.add(new_card)
            db.session.commit()
        
            return redirect(url_for('passStatus'))
    return render_template("passcardRegister.html", user=current_user, flag=flag)

@app.route("/passStatus", methods=['GET', 'POST'])
@login_required
def passStatus():
    user=current_user
    card = PassCard.query.filter_by(user_id=user.id).first()
    if card:
        return render_template("pass_status.html", user=current_user, card=card)
    else:
        return redirect(url_for('AddCard'))
    
@app.route("/AddCard", methods=['GET', 'POST'])
@login_required
def AddCard():
    user=current_user
    card = PassCard.query.filter_by(user_id=user.id).first()
    if card:
        if request.method == 'POST':
            card = PassCard.query.filter_by(user_id=user.id).first()
            card_no = request.form.get('card_no')
            card_type = request.form.get('card_type')
            if card_no == card.card_no and card_type == card.card_type:
                card.card_view = 1
            return redirect(url_for('passStatus'))
        return render_template("AddCard.html", user=current_user,)
    else:
        return redirect(url_for('passcardRegister'))
    
@app.route("/recharge", methods=['GET', 'POST'])
@login_required
def recharge():
    user=current_user
    card = PassCard.query.filter_by(user_id=user.id).first()
    if card:
        if request.method == 'POST':
            wallet_type = request.form.get('wallet')
            card_no = int(request.form.get('card_no'))
            c = int(card.card_no)
            wallet_mobile = request.form.get('mobile')
            amount = request.form.get('amount')
            trxid = request.form.get('trxid')
            if card_no == c:
                new_recharge = Recharge(wallet_type=wallet_type, card_no=card_no, wallet_mobile=wallet_mobile, trxid=trxid, recharge_amount=amount, card_id=card.id, user_id=user.id, status='Pending')
                db.session.add(new_recharge)
                db.session.commit()
                return redirect(url_for('index'))
            else:
                return render_template("AddCard.html", user=current_user)


        return render_template("recharge.html", user=current_user, card=card)
    else:
        return redirect(url_for('passcardRegister'))

@app.route("/rechargeHistory", methods=['GET', 'POST'])
@login_required
def rechargeHistory():
    user=current_user
    card = PassCard.query.filter_by(user_id=user.id).first()
    r_history = Recharge.query.filter_by(user_id=user.id).all()
    if card:
        return render_template("rechargeHistory.html", user=current_user, card=card, r_history=r_history)
    else:
        return redirect(url_for('passcardRegister'))
    
    return render_template("rechargeVerification.html", user=current_user, card=card, r_history=r_history)
    
@app.route("/rechargeVerification", methods=['GET', 'POST'])
@login_required
def rechargeVerification():
    user=current_user
    card = PassCard.query.filter_by(user_id=user.id).first()
    r_history = Recharge.query.all()
    
    
    return render_template("rechargeVerification.html", user=current_user, card=card, r_history=r_history)
    
@app.route("/rechargeSuccess/<int:id>", methods=['GET', 'POST'])
@login_required
def rechargeSuccess(id):
    user=current_user
    card = PassCard.query.filter_by(user_id=user.id).first()
    r_history = Recharge.query.filter_by(user_id=user.id).all()


    r = Recharge.query.get_or_404(id)
    if r:
        r.status = 'Success'
        uid = r.user_id
        up = PassCard.query.filter_by(user_id=uid).first()
        up.card_balance = up.card_balance + r.recharge_amount # a = a + b
        db.session.commit()
        return redirect(url_for('rechargeVerification'))
    else:
        return redirect(url_for('passcardRegister'))
    
@app.route("/stationManagement", methods=['GET', 'POST'])
@login_required
def stationManagement():
    user=current_user
    stations = Station.query.all()
    if request.method == 'POST':
        station_name = request.form.get('name')
        station_serial = request.form.get('serial')
        new_station = Station(station_name=station_name, station_serial=station_serial)
        db.session.add(new_station)
        db.session.commit()
        return redirect(url_for('stationManagement'))
    return render_template("stationManagement.html", user=current_user, stations=stations)

@app.route("/stationdelete/<int:id>", methods=['GET', 'POST'])
@login_required
def stationdelete(id):
    user=current_user
    station = Station.query.get_or_404(id)
    db.session.delete(station)
    db.session.commit()
    return redirect(url_for('stationManagement'))

@app.route("/trip", methods=['GET', 'POST'])
@login_required
def trip():
    user=current_user
    stations = Station.query.all()
    if request.method == 'POST':
        start = request.form.get('sname')
        dest = request.form.get('dname')
        trip_date = request.form.get('date')
        trip_time = request.form.get('time')
        print(trip_time)
        trip_user = user.id
        s_station = Station.query.filter_by(station_name=start).first()
        d_station = Station.query.filter_by(station_name=dest).first()
        s = int(s_station.station_serial)
        d = int(d_station.station_serial)
        diff = d - s
        total_trip_time = Trip.query.filter_by(trip_time=trip_time).all()
        print(total_trip_time)

        if len(total_trip_time)>3:
            return redirect(url_for('tripFull'))

        if diff <= 0:
            pass
        else:
            trip_fare = diff * 10
            return redirect(url_for('routeandfare', trip_fare=trip_fare, trip_date=trip_date, start=start, dest=dest, trip_user=trip_user, trip_time=trip_time,s=s,d=d))

        return redirect(url_for('trip'))
    return render_template("trip.html", user=current_user, stations=stations)

@app.route("/routeandfare", methods=['GET', 'POST'])
@login_required
def routeandfare():
    user=current_user
    stations = Station.query.all()
    trip_fare = request.args.get('trip_fare')
    trip_date = request.args.get('trip_date')
    start = request.args.get('start')
    dest = request.args.get('dest')
    trip_user = request.args.get('trip_user')
    trip_time = request.args.get('trip_time')
    s = request.args.get('s')
    d = request.args.get('d')
    ts = Station.query.filter_by(station_serial=s).first()
    td = Station.query.filter_by(station_serial=d).first()
    card = PassCard.query.filter_by(user_id=user.id).first()
    if card:
        new_trip = Trip(trip_date=trip_date, start=start, dest=dest, trip_fare=trip_fare, trip_card=card.card_no, trip_user=trip_user, trip_status='Pending payment', payment_status='Unpaid', trip_time=trip_time)
        db.session.add(new_trip)
        db.session.commit()
        return render_template("routeandfare.html", user=current_user, stations=stations, trip_fare=trip_fare, trip_date=trip_date, start=start, dest=dest, trip_user=trip_user, trip_time=trip_time, ts=ts.id, td=td.id)

    else:
        return redirect(url_for('passcardRegister'))

   
@app.route("/tripHistory", methods=['GET', 'POST'])
@login_required
def tripHistory():
    user=current_user
    trips = Trip.query.filter_by(trip_user=user.id).all()
    return render_template("tripHistory.html", user=current_user, trips=trips)
            

@app.route("/paynow/<int:id>", methods=['GET', 'POST'])
@login_required
def paynow(id):
    user=current_user
    card = PassCard.query.filter_by(user_id=user.id).first()
    trip = Trip.query.get_or_404(id)
    if trip:
        if card.card_balance < trip.trip_fare:
            return redirect(url_for('recharge'))
        card.card_balance = card.card_balance - trip.trip_fare
        trip.payment_status = 'Paid'
        trip.trip_status = 'Scheduled'
        db.session.commit()
        return redirect(url_for('tripHistory'))
    else:
        return redirect(url_for('tripHistory'))


@app.route("/addVoucher", methods=['GET', 'POST'])
@login_required
def addVoucher():
    user=current_user
    if request.method == 'POST':
        voucher_code = request.form.get('vcode')
        voucher_amount = request.form.get('vamount')
        voucher_admin =user.username
        new_voucher = voucher(voucher_code=voucher_code, voucher_amount=voucher_amount, voucher_status="Eligible",voucher_admin=voucher_admin)
        db.session.add(new_voucher)
        db.session.commit()
        return redirect(url_for('allVoucher'))
    return render_template("addVoucher.html", user=current_user)

@app.route("/allVoucher", methods=['GET', 'POST'])
@login_required
def allVoucher():
    user=current_user
    vouchers = voucher.query.all()
    return render_template("allVoucher.html", user=current_user, vouchers=vouchers)

@app.route("/voucherUpdate/<int:id>", methods=['GET', 'POST'])
@login_required
def voucherUpdate(id):
    user=current_user
    voucher_code = voucher.query.get_or_404(id)
    if voucher_code:
        voucher_code.voucher_status = 'Uneligible'
        print(voucher_code.voucher_status)
        db.session.commit()
        return redirect(url_for('allVoucher'))
    else:
        return redirect(url_for('allVoucher'))

@app.route("/applyVoucher/<int:id>", methods=['GET', 'POST'])
@login_required
def applyVoucher(id):
    trip = Trip.query.get_or_404(id)
    if request.method == 'POST':
        voucher_code1 = request.form.get('vcode')
        c2 = voucher.query.filter_by(voucher_code=voucher_code1).first()
        if c2 and c2.voucher_status == 'Eligible':
            trip.trip_fare = trip.trip_fare - (trip.trip_fare * (c2.voucher_amount/100))
            db.session.commit()
            return redirect(url_for('tripHistory'))
        else:
            return redirect(url_for('tripHistory'))
    return render_template("applyVoucher.html", user=current_user,id=id)


@app.route("/tripComplete/<int:id>", methods=['GET', 'POST'])
@login_required
def tripComplete(id):
    user=current_user
    trip = Trip.query.get_or_404(id)
    if trip:
        trip.trip_status = 'Completed'
        db.session.commit()
        return redirect(url_for('tripHistory'))
    else:
        return redirect(url_for('tripHistory'))

@app.route("/tripCancel/<int:id>", methods=['GET', 'POST'])
@login_required
def tripCancel(id):
    user=current_user
    trip = Trip.query.get_or_404(id)
    if trip:
        trip.trip_status = 'Cancelled'
        db.session.commit()
        return redirect(url_for('tripHistory'))
    else:
        return redirect(url_for('tripHistory'))

@app.route("/tripFull", methods=['GET', 'POST'])
@login_required
def tripFull():
    user=current_user
    return render_template("tripFull.html", user=current_user)

@app.route("/issueRefund/<int:id>", methods=['GET', 'POST'])
@login_required
def issueRefund(id):
    trip = Trip.query.get_or_404(id)
    r_username = User.query.filter_by(id=trip.trip_user).first()
    print(r_username.username)
    if trip:
        r1 = refund.query.filter_by(trip_id=id).first()
        if r1:
            pass
        else:
            new_refund = refund(refund_amount=(trip.trip_fare - (trip.trip_fare * 0.5)), trip_id=id, trip_user=r_username.username)
            trip.trip_status = 'Refund Issued'
            db.session.add(new_refund)
            db.session.commit()
        return redirect(url_for('tripHistory'))
    else:
        return redirect(url_for('tripHistory'))

@app.route("/refundVerification", methods=['GET', 'POST'])
@login_required
def refundVerification():
    refunds = refund.query.all()
    return render_template("refundVerification.html", user=current_user, refunds=refunds)

@app.route("/refundSuccess/<int:id>", methods=['GET', 'POST'])
@login_required
def refundSuccess(id):
    r = refund.query.get_or_404(id)
    trip = Trip.query.filter_by(id=r.trip_id).first()
    refund_card = PassCard.query.filter_by(user_id=trip.trip_user).first()
    if r:
        r.refund_status = 'Refunded'
        trip.trip_status = 'Refunded'
        refund_card.card_balance = refund_card.card_balance + r.refund_amount
        db.session.commit()
        return redirect(url_for('refundVerification'))
    else:
        return redirect(url_for('refundVerification'))
    
@app.route("/refundList", methods=['GET', 'POST'])
@login_required
def refundList():
    user = current_user
    refunds = refund.query.filter_by(trip_user=user.username).all()
    return render_template("refundList.html", user=current_user, refunds=refunds)

@app.route("/UserList", methods=['GET', 'POST'])
@login_required
def UserList():
    users = User.query.filter_by(aType="Regular User").all()
    return render_template("UserList.html", user=current_user, users=users)

@app.route("/UserBan/<int:id>", methods=['GET', 'POST'])
@login_required
def UserBan(id):
    user = User.query.get_or_404(id)
    if user:
        user.aStatus = 'Banned'
        db.session.commit()
        return redirect(url_for('UserList'))
    
@app.route("/UserUnban/<int:id>", methods=['GET', 'POST'])
@login_required
def UserUnban(id):
    user = User.query.get_or_404(id)
    if user:
        user.aStatus = 'Unbanned'
        db.session.commit()
        return redirect(url_for('UserList'))

@app.route("/writeComplain", methods=['GET', 'POST'])
@login_required
def writeComplain():
    user = current_user
    if request.method == 'POST':
        complain = request.form.get('comp')
        new_complain = Complains(complain=complain, user_id=user.id)
        db.session.add(new_complain)
        db.session.commit()
        return redirect(url_for('profile'))
    return render_template("writeComplain.html", user=current_user)

@app.route("/complainList", methods=['GET', 'POST'])
@login_required
def complainList():
    complains = Complains.query.all()
    return render_template("complainList.html", user=current_user, complains=complains)

@app.route("/complainReply/<int:id>", methods=['GET', 'POST'])
@login_required
def complainReply(id):
    complain = Complains.query.get_or_404(id)
    if request.method == 'POST':
        reply = request.form.get('reply')
        complain.reply = reply
        complain.status = 'Replied'
        db.session.commit()
        return redirect(url_for('complainList'))
    return render_template("complainReply.html", user=current_user, complain=complain)

@app.route("/complainListUser", methods=['GET', 'POST'])
@login_required
def complainListUser():
    user = current_user
    complains = Complains.query.filter_by(user_id=user.id).all()
    return render_template("complainListUser.html", user=current_user, complains=complains)

if __name__ == '__main__':
    app.run(debug=True)