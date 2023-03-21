from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, RadioField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from sevaapp.models import User

# This form stores the user or volunteer information which will be useful further
class RegistrationForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=2, max=20)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    role = StringField("Role")
    address = StringField("Address", validators=[DataRequired()])
    pincode = StringField("Pincode", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Sign Up")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data, role=self.role.data).first()
        if user:
            raise ValidationError(
                "That username is taken. Please choose a different one."
            )

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data, role=self.role.data).first()
        if user:
            raise ValidationError("That email is taken. Please choose a different one.")

# This form takes the email and password of a user or volunteer to get authenticated
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    role = StringField("Role")
    submit = SubmitField("Login")

# This form take username as input for volunteer and if 
# the user is not assigned any monitoring features then volunteer can 
# add user to the monitoring 
class MonitoringForm(FlaskForm):
    patient = StringField(
        "Username", validators=[DataRequired(), Length(min=2, max=20)]
    )
    submit = SubmitField("Submit")

# This form stores the data if user had taken medicine for the day or not 
class MedicineTakenForm(FlaskForm):
    med_taken = RadioField("option", choices=[("Yes", "Yes"), ("No", "No")])
    submit = SubmitField("Submit")
