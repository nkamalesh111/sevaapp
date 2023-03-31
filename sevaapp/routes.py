from flask import render_template, url_for, flash, redirect, request
from sevaapp import app, db, bcrypt, socketio
from sevaapp.forms import (
    RegistrationForm,
    LoginForm,
    MonitoringForm,
    MedicineTakenForm,
)
from sevaapp.models import User, Notification
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime
from dateutil import relativedelta
# FOR SIGN IN AND SIGN UP
####################################################################
# Creates a table in databease
@app.before_first_request
def create_tables():
    db.create_all()

# Home page
@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html", title="Home")

# About page store about project's information
@app.route("/about")
def about():
    return render_template("about.html", title="About")

# Route to registraion of a user or volunteer
@app.route("/register/<role>", methods=["GET", "POST"])
def register(role):
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = RegistrationForm()
    form.role.data = role
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user = User(
            firstname=form.f_name.data,
            lastname=form.l_name.data,
            username=form.f_name.data.lower()+form.l_name.data.lower(),
            number=form.number.data,
            pincode=form.pincode.data,
            password=hashed_password,
            role=form.role.data,
            address=form.address.data,
            counter=0,
        )
        db.session.add(user)
        db.session.commit()
        flash("Your account has been created! You are now able to log in", "success")
        return redirect(url_for("login", role=role))
    return render_template("register.html", title=f"{role} Register", form=form)

# Login route where onn the basis of role of a person the system authenticates as user or volunteer
@app.route("/login/<role>", methods=["GET", "POST"])
def login(role):
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = LoginForm()
    form.role.data = role
    if form.validate_on_submit():
        user = User.query.filter_by(number=form.number.data, role=form.role.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=True)
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("account"))
        else:
            flash("Login Unsuccessful. Please check number and password", "danger")
    return render_template("login.html", title=f"{role} Login", form=form)

# Logout from the user or volunteer account
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

# A person can see his/ her personal details here
@app.route("/account")
@login_required
def account():
    return render_template("account.html", title="Account")

# FOR COMMUNICATION BETWEEN USER AND VOLUNTEERS
#######################################################################################
@socketio.on("logged_in")
def handle_logged_in_event(data):
    if data["url"] == url_for("help"):
        socketio.emit("announcement", data["pin"], include_self=False)


@socketio.on("notify")
def handle_notify_event(data):
    data['num']=User.query.filter_by(id=data['id']).first().number
    socketio.emit("notify_user", data, include_self=False)


@app.route("/help")
@login_required
def help():
    n = Notification.query.filter_by(user_id=current_user.id).first()
    n = Notification(
        user_id=current_user.id,
        date1=str(datetime.now().date()),
        time1=str(datetime.now().time()),
        action="no",
        pincode=current_user.pincode,
    )
    db.session.add(n)
    db.session.commit()
    return render_template("home.html", title="home")


@app.route("/notifications/<title>")
@login_required
def notifications(title):
    n = (
        Notification.query.filter_by(pincode=current_user.pincode, action="no")
        .order_by(Notification.date1.desc(), Notification.time1.desc())
        .all()
    )
    return render_template("display.html", n=n, title=title)


@app.route("/details/<id>/<date>/<time>")
@login_required
def details(id, date, time):
    usr = User.query.filter_by(id=id).first()
    return render_template(
        "user_details.html", usr=usr, date=date, time=time, text="accept"
    )


@app.route("/ack/<usr_id>/<date>/<time>")
@login_required
def ack(usr_id, date, time):
    n = Notification.query.filter_by(
        pincode=current_user.pincode,
        user_id=usr_id,
        date1=date,
        time1=time,
    ).first()
    if n.action == "no":
        n.action = "yes"
        n.date2 = str(datetime.now().date())
        n.time2 = str(datetime.now().time())
        n.volunteer_id = current_user.id
        db.session.commit()
        return render_template(
            "user_details.html",
            usr=User.query.filter_by(id=usr_id).first(),
            date=date,
            time=time,
            text=f"accepted by volunteer {current_user.firstname} {current_user.lastname}",
        )
    v=User.query.filter_by(id=n.volunteer_id).first()
    return render_template(
        "user_details.html",
        usr=User.query.filter_by(id=usr_id).first(),
        date=date,
        time=time,
        text=f"already accepted by volunteer {v.firstname} {v.lastname}",
    )

# FOR ADHERENCE MONITORING
#############################################################################################
# This function enables a volunteer to monitor a user
@app.route("/monitor", methods=["GET", "POST"])
@login_required
def monitor():
    user_name = User.query.filter_by(role='User').all()
    # print(name)
    namelst = [(i.id,i.username) for i in user_name]
    
    form = MonitoringForm()
    form.userid.choices = namelst
    if form.validate_on_submit():
        
        if user := User.query.filter_by(id=form.userid.data,role='User').first():
            print(user)
            if user.monitoring_applied == 'No':
                user.monitoring_applied = 'Yes'
                user.counter = 0
                user.date = str(datetime.now().date())
                db.session.commit()
                flash(
                    f'Monitoring is applied successfully for {user.username}', 'success')
            else:
                flash(f'Patient: {user.username} is already been monitored', 'warning')
            patient_status()
            return redirect(url_for('home'))
        else:
            flash('Check patient username', 'danger')
        patient_status()
    patient_status()
    return render_template('monitoring.html', title='Monitoring', form=form )

# It will alert the user if user has not submitted the form for 3 or more days
def patient_status():
    user = User.query.filter_by(monitoring_applied='Yes').all()
    date1, date2 = 0, 0
    for i in user:
        today = str(datetime.now().date())
        # print(type(today))

        date1 = datetime.strptime(i.date, "%Y-%m-%d")
        date2 = datetime.strptime(today, "%Y-%m-%d")
        difference = relativedelta.relativedelta(date2, date1)
        if (i.counter + difference.days) >= 3:
            flash(f'{i.firstname} {i.lastname} has skipped the medication', 'danger')
    return redirect(url_for('home'))


# This function will store the user's choice, whether he has taken medicine or not for the given day only. 
@app.route("/med_taken", methods=["GET", "POST"])
@login_required
def med_taken():
    user = User.query.filter_by(id=current_user.id, role="User").first()
    if user.monitoring_applied == "Yes":
        today = str(datetime.now().date())
        if user.date <= today:# to check that patient should not enter twice the form for the same date
            form = MedicineTakenForm()
            if form.validate_on_submit():
                if form.med_taken.data == "No":
                    user.counter += 1 # counts how many days 
                tomorrow = datetime.strptime(today, "%Y-%m-%d") + relativedelta.relativedelta(days=1)
                tomorrow = tomorrow.strftime("%Y-%m-%d")
                user.date = tomorrow
                db.session.commit()
                flash(
                    "Your daily monitoring has been checked successfully :) ", "success"
                )
                return redirect(url_for("home"))
            return render_template(
                "med_taken.html",
                title="Medicine_Taken",
                form=form,
            )
        else:
            flash("You have already submitted your option for today.", "warning")
            return redirect(url_for("home"))
    else:
        flash("Doctor has not assigned any monitoring on you", "warning")
        return redirect(url_for("home"))
