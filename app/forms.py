from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SubmitField, FormField, FieldList
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User
from app.game_forms import PowerGridForm

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    displayname = StringField('Display Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')
    
    def validate_displayname(self, displayname):
        user = User.query.filter_by(displayname=displayname.data).first()
        if user is not None:
            raise ValidationError('Please use a different display name.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class EditProfileForm(FlaskForm):
    displayname = StringField('Display Name', validators=[DataRequired()])
    about_me = TextAreaField('About Me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_displayname(self, displayname):
        if displayname.data != self.original_username:
            user = User.query.filter_by(displayname=displayname.data).first()
            if user is not None:
                raise ValidationError('Please use a different display name.')

class SubmitMatchForm(FlaskForm):
    game = StringField('Game', validators=[DataRequired()])
    stats = StringField('Test')
    submit = SubmitField('Submit')
    
class PowerGridScore(FlaskForm):
    scores = FieldList(FormField(PowerGridForm), max_entries=6)
    submit = SubmitField('Submit')

