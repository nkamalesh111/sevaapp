from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, RadioField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from sevaapp.models import User
import phonenumbers

# This form stores the user or volunteer information which will be useful further
class RegistrationForm(FlaskForm):
    f_name = StringField("First Name", validators=[DataRequired()])
    l_name = StringField("Last Name", validators=[DataRequired()])
    username = StringField("username")
    number = StringField("Phone Number", validators=[DataRequired()])
    address = StringField("Address", validators=[DataRequired()])
    role = StringField("Role")
    pincode = StringField("Pincode", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Sign Up")

    def validate_number(self, phone):
        try:
            p = phonenumbers.parse(phone.data)
            if not phonenumbers.is_valid_number(p):
                raise ValueError()
            else:
                p = User.query.filter_by(number=phone.data,role=self.role.data).first()
                if p:
                    raise ValidationError('phone number already exists. Please choose another one.')      
        except (phonenumbers.phonenumberutil.NumberParseException, ValueError):
            raise ValidationError('Invalid phone number')

    def validate_username(self,f_name):
        usr = User.query.filter_by(firstname=f_name.data,lastname=self.l_name.data,role=self.role.data).first()
        if usr:
            raise ValidationError('firstname and lastname are chosen. Please choose a different one.')
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
    patient = StringField(
        "Username", validators=[DataRequired()]
    )
    submit = SubmitField("Submit")

# This form stores the data if user had taken medicine for the day or not 
class MedicineTakenForm(FlaskForm):
    med_taken = RadioField("option", choices=[("Yes", "Yes"), ("No", "No")])
    submit = SubmitField("Submit")
