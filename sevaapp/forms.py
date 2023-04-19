from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, RadioField, SelectField, IntegerField
from wtforms.validators import DataRequired,  EqualTo, ValidationError
from sevaapp.models import User
import phonenumbers
import re

# This form stores the user or volunteer information which will be useful further
class RegistrationForm(FlaskForm):
    f_name = StringField("First Name", validators=[DataRequired()])
    l_name = StringField("Last Name", validators=[DataRequired()])
    username = StringField("username")
    number = StringField("Phone Number", validators=[DataRequired()])
    address = StringField("Address", validators=[DataRequired()])
    role = StringField("Role")
    pincode = IntegerField("Pincode", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Sign Up")

    def validate_number(self,num):
        try:
            p = phonenumbers.parse(num.data)
            if not phonenumbers.is_valid_number(p):
                raise ValidationError('Invalid phone number')
            if p := User.query.filter_by(
                number=num.data, role=self.role.data
            ).first():
                raise ValidationError('phone number already exists. Please choose another one.')
        except phonenumbers.phonenumberutil.NumberParseException as e:
            raise ValidationError('Invalid phone number') from e
    def validate_username(self,f):
        if usr := User.query.filter_by(
            firstname=f.data, lastname=self.l_name.data, role=self.role.data
        ).first():
            raise ValidationError('firstname and lastname are chosen. Please choose a different one.')
    def validate_pincode(self,pin):
        regex = "^[1-9]{1}[0-9]{2}\\s{0,1}[0-9]{3}$";
        m = re.match(regex, str(pin.data))
        if m is None:
            raise ValidationError('Invalid pincode')
        else:
            return True
# This form takes the email and password of a user or volunteer to get authenticated
class LoginForm(FlaskForm):
    number = StringField("number", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    role = StringField("Role")
    submit = SubmitField("Login")

# This form take username as input for volunteer and if 
# the user is not assigned any monitoring features then volunteer can 
# add user to the monitoring 
class MonitoringForm(FlaskForm):
    userid = SelectField('Patient name', validators=[DataRequired()] , coerce=int)
    submit = SubmitField("Submit")

# This form stores the data if user had taken medicine for the day or not 
class MedicineTakenForm(FlaskForm):
    med_taken = RadioField("option", choices=[("Yes", "Yes"), ("No", "No")])
    submit = SubmitField("Submit")
