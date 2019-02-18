from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from app.models import User, Problem, Contest, Inform, Record

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class Commit(FlaskForm):
    language = SelectField('Language', choices=[
        ('C++', 'C++'),
        ('C', 'C')
    ])
    code= TextAreaField('Code', validators=[Length(min=0, max=65535)])
    submit = SubmitField('提交')

class AddProblem(FlaskForm):
    title = StringField('Title', validators=[Length(min=0, max=255)])
    ms = StringField('MS', [DataRequired()])
    kb = StringField('KB', [DataRequired()])
    content = TextAreaField('Content', validators=[Length(min=0, max=65535)])
    source = StringField('Source', [DataRequired()])
    hint = TextAreaField('Hint', validators=[Length(min=0, max=255)])
    submit = SubmitField('提交')

class AddContest(FlaskForm):
    title = StringField('Title', validators=[Length(min=0, max=127)])
    content = TextAreaField('Content', validators=[Length(min=0, max=65535)])
    source = StringField('Source', validators=[Length(min=0, max=127)])
    submit = SubmitField('提交')

class AddContestProblem(FlaskForm):
    contest_id = StringField('Contest ID', validators=[Length(min=0, max=127)])
    problem_id = StringField('Problem ID', validators=[Length(min=0, max=127)])
    submit = SubmitField('提交')

class AddInform(FlaskForm):
    title = StringField('Title', validators=[Length(min=0, max=127)])
    source = StringField('Source', validators=[Length(min=0, max=127)])
    content = TextAreaField('Content', validators=[Length(min=0, max=65535)])
    submit = SubmitField('提交')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')