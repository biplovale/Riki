"""
    Forms
    ~~~~~
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import BooleanField
from wtforms import StringField
from wtforms import TextAreaField
from wtforms import PasswordField
from wtforms.validators import InputRequired, EqualTo, Email
from wtforms.validators import ValidationError

from wiki.core import clean_url
from wiki.web import current_wiki
from wiki.web import current_users


class URLForm(FlaskForm):
    url = StringField('', validators=[InputRequired()])

    def validate_url(self, field):
        if current_wiki.exists(field.data):
            raise ValidationError('The URL "%s" exists already.' % field.data)

    def clean_url(self, url):
        return clean_url(url)


class SearchForm(FlaskForm):
    term = StringField('', validators=[InputRequired()])
    ignore_case = BooleanField(
        description='Ignore Case',
        # FIXME: default is not correctly populated
        default=True)
    search_by_author = BooleanField(
        description='Search by Author',
        default=False
    )


class EditorForm(FlaskForm):
    title = StringField('', [InputRequired()])
    content = TextAreaField('', [InputRequired()])
    tags = StringField('')
    image = FileField('')


class LoginForm(FlaskForm):
    name = StringField('', validators=[InputRequired()])
    password = PasswordField('', validators=[InputRequired()])

    def validate_name(self, field):
        user = current_users.get_user(field.data)
        if not user:
            raise ValidationError('This username does not exist.')

    def validate_password(self, field):
        user = current_users.get_user(self.name.data)
        if not user:
            return
        if not user.check_password(field.data):
            raise ValidationError('Username and password do not match.')


class SignUpForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[InputRequired(), EqualTo('password')])
