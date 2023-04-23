from flask import render_template, url_for, flash, redirect, request, copy_current_request_context
from sevaapp import app, db, bcrypt, socketio
from sevaapp.forms import (
    RegistrationForm,
    LoginForm,
    MonitoringForm,
    MedicineTakenForm,
    DeleteForm,
)
from sevaapp.models import User, Notification
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime
from dateutil import relativedelta
import time, gevent
# FOR SIGN IN AND SIGN UP
####################################################################
d={}

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

# Route to registration of a user or volunteer
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
        try:
            logout_user()
        finally:
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

#to delete account
@app.route("/delete", methods=['GET', 'POST'])
@login_required
def delete():
    if request.method != 'POST':
        return render_template('delete_account.html')
    User.query.filter_by(id=current_user.id).delete()
    db.session.commit()
    flash("Account deleted successfully 👍","success")
    return redirect(url_for('home'))
    

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

@app.route("/update_account/<role>", methods=["GET", "POST"])
@login_required
def update_account(role):
    # if current_user.is_authenticated:
    #     return redirect(url_for("home"))
    tmp=User.query.filter_by(id=current_user.id).first()
    form = RegistrationForm()
    form.role.data = role
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        
        tmp.firstname=form.f_name.data
        tmp.lastname=form.l_name.data
        tmp.username=form.f_name.data.lower()+form.l_name.data.lower()
        tmp.number=form.number.data
        tmp.pincode=form.pincode.data
        tmp.password=hashed_password
        tmp.role=form.role.data
        tmp.address=form.address.data
        db.session.commit()
        flash("Your account has been updated successfully", "success")
        flash("logged out", "success")
        return redirect(url_for("logout"))
    return render_template("update_account.html", title=f"{role} update_account", form=form)

    
# FOR COMMUNICATION BETWEEN USER AND VOLUNTEERS
#######################################################################################

@socketio.on("logged_in")
def handle_logged_in_event(data):
    if (data["url"] != url_for("help")) or (len(Notification.query.filter_by(user_id=data["id"],action="no").all()))>1:
        return
    d[data["id"]]=[0,[]]
    @copy_current_request_context
    def chk(a,b):
        while True:
            q=User.query.filter(User.pincode.notin_(d[a][1]),User.role=='Volunteer').with_entities(User.pincode).all()
            if q:
                distances=[abs(int(b)-i[0]) for i in q]
                closest_pincode=q[distances.index(min(distances))][0]
                d[a][1].append(closest_pincode)
            else:
                break
            socketio.emit("announcement", d[a][1][-1], include_self=False)
            time.sleep(30)
            if d[a][0]==1:
                break

    gevent.spawn(chk,data["id"],data["pin"])


@socketio.on("notify")
def handle_notify_event(data):
    data['num']=User.query.filter_by(id=data['id2']).first().number
    socketio.emit("notify_user", data, include_self=False)


@app.route("/help")
@login_required
def help():
    n = Notification.query.filter_by(user_id=current_user.id,action="no").first()
    if n is None:
        n = Notification(user_id=current_user.id,action="no")
        db.session.add(n)
        db.session.commit()
    return render_template("home.html", title="home")


@app.route("/notifications/<title>")
@login_required
def notifications(title):
    n = (
        Notification.query.filter_by(action="no")
        .order_by(Notification.id.desc()).with_entities(Notification.id,Notification.user_id)
        .all()
    )
    tmp=[i.user_id for i in n]
    # tmp=list(dict.fromkeys(tmp))
    u = User.query.filter(User.id.in_(tmp)).with_entities(User.firstname,User.lastname).all()
    return render_template("display.html", n=n, u=u, title=title)


@app.route("/details/<id1>/<id2>")
@login_required
def details(id1,id2):
    usr = User.query.filter_by(id=id1).first()
    return render_template(
        "user_details.html", usr=usr, id=id2, text="accept"
    )


@app.route("/ack/<usr_id>/<v_id>")
@login_required
def ack(usr_id,v_id):
    n = Notification.query.filter_by(
        user_id=usr_id,id=v_id
    ).first()
    if n.action == "no":
        d[usr_id][0]=1
        n.action = "yes"
        n.volunteer_id = current_user.id
        n.pincode = current_user.pincode
        db.session.commit()
        return render_template(
            "user_details.html",
            usr=User.query.filter_by(id=usr_id).first(),
            text=f"accepted by volunteer {current_user.firstname} {current_user.lastname}",
        )
    v=User.query.filter_by(id=n.volunteer_id).first()
    return render_template(
        "user_details.html",
        usr=User.query.filter_by(id=usr_id).first(),
        text=f"already accepted by volunteer {v.firstname} {v.lastname}",
    )

# FOR ADHERENCE MONITORING
#############################################################################################
# This function enables a volunteer to monitor a user
@app.route("/monitor", methods=["GET", "POST"])
@login_required
def monitor():
    if current_user.role=='Volunteer':
        user_name = User.query.filter_by(role='User').all()
        namelst = [(i.id,i.username) for i in user_name]
        
        form = MonitoringForm()
        form.userid.choices = namelst
        if form.validate_on_submit():
            
            if user := User.query.filter_by(id=form.userid.data,role='User').first():
                if user.date is None:
                    user.counter = 0
                    user.startdate = str(form.startdate.data)
                    user.date = user.startdate
                    user.enddate = str(form.enddate.data)
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
    flash('You can\'t access this page','danger')
    return redirect(url_for('home'))

# It will alert the user if user has not submitted the form for 3 or more days
def patient_status():
    user = User.query.filter(User.date!=None).all()
    date1, date2 = 0, 0
    for i in user:
        today = str(datetime.now().date())
        # print(type(today))

        date1 = datetime.strptime(i.startdate, "%Y-%m-%d")
        date2 = datetime.strptime(today, "%Y-%m-%d")
        difference = relativedelta.relativedelta(date2, date1)
        if (i.counter + difference.days) >= 3:
            flash(f'{i.firstname} {i.lastname} has skipped the medication for {i.counter + difference.days} days', 'danger')
    return redirect(url_for('home'))

@app.route('/deletemon', methods=["GET", "POST"])
@login_required
def deletemon():
    if current_user.role=='Volunteer':
        user_name = User.query.filter(User.date !=None, User.role=='User').all()
        namelst = [(i.id,i.username) for i in user_name]
        form = DeleteForm()
        form.userid.choices = namelst
        if form.validate_on_submit():
            
            if user := User.query.filter_by(id=form.userid.data,role='User').first():
                user.counter = 0
                user.startdate,user.enddate = None,None
                user.date = user.startdate
                db.session.commit()
                flash(f'Monitoring deletion is done successfully for {user.username}', 'success')
                return redirect(url_for('home'))
        return render_template('deletemon.html', title='Delete', form=form )
    flash('You can\'t access this page', 'danger')
    return redirect(url_for('home'))
    
    
# This function will store the user's choice, whether he has taken medicine or not for the given day only. 
@app.route("/med_taken", methods=["GET", "POST"])
@login_required
def med_taken():
    user = User.query.filter_by(id=current_user.id, role="User").first()
    today = str(datetime.now().date())
    if user.date is not None and (today >= user.startdate and today <= user.enddate):
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
