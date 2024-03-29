from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, RadioField, SelectField, DateField, IntegerField
from wtforms.validators import DataRequired,  EqualTo, ValidationError
from sevaapp.models import User
import phonenumbers, string
import re
from datetime import date
from flask import flash


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
    def validate_f_name(self,f):
        if usr := User.query.filter_by(firstname=self.f_name.data, role=self.role.data).first():
            raise ValidationError('firstname is already chosen. Please choose a different one.')
    def validate_l_name(self,f):
        if usr := User.query.filter_by(lastname=self.l_name.data, role=self.role.data).first():
            raise ValidationError('lastname is already chosen. Please choose a different one.')    
    def validate_pincode(self,pin):
        regex = "^[1-9]{1}[0-9]{2}\\s{0,1}[0-9]{3}$";
        m = re.match(regex, str(pin.data))
        if m is None:
            raise ValidationError('Invalid pincode')
        else:
            return True
        
    def validate_password(self,password):
        if len(password.data) < 8:
            raise ValidationError('minimum length is 8 characters')
        if not any(char.isupper() for char in password.data):
            raise ValidationError('atleast one upper case character is required')
        if not any(char.islower() for char in password.data):
            raise ValidationError('atleast one lower case character is required')
        if not any(char.isdigit() for char in password.data):
            raise ValidationError('atleast one digit is required')
        if all(char not in string.punctuation for char in password.data):
            raise ValidationError('atleast one symbol is required')
        return True
# This form takes the email and password of a user or volunteer to get authenticated
class LoginForm(FlaskForm):
    number = StringField("Number", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    role = StringField("Role")
    submit = SubmitField("Login")

# This form take username as input for volunteer and if 
# the user is not assigned any monitoring features then volunteer can 
# add user to the monitoring 
class MonitoringForm(FlaskForm):
    userid = SelectField('Patient name', validators=[DataRequired()] , coerce=int)
    startdate = DateField('start date',format='%Y-%m-%d',validators=[DataRequired()])
    enddate = DateField('end date',format='%Y-%m-%d',validators=[DataRequired()])
    submit = SubmitField("Submit")
    
    def validate_startdate(self,startdate):
        today = date.today()
        if (startdate.data - today).days < 0:
            raise ValidationError("please enter today's date or future dates")
    def validate_enddate(self,enddate):
        if (self.startdate.data - enddate.data).days > 0:
            raise ValidationError("please enter valid date which ids greater than start date")

# This form stores the data if user had taken medicine for the day or not 
class MedicineTakenForm(FlaskForm):
    med_taken = RadioField("option", choices=[("Yes", "Yes"), ("No", "No")])
    submit = SubmitField("Submit")

class DeleteForm(FlaskForm):
    userid = SelectField('Patient name', validators=[DataRequired()] , coerce=int)
    submit = SubmitField("Submit")