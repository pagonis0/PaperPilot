from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FileField, validators, DateField, TimeField
from wtforms.validators import DataRequired, ValidationError
from blog.models import User, Paper
from wtforms_components import SelectField
from datetime import datetime

class LoginForm(FlaskForm):
    user_name_pid = StringField('', validators=[validators.InputRequired()],
                                render_kw={'autofocus': True, 'placeholder': 'Username'})

    user_pid_Password = PasswordField('', validators=[validators.InputRequired()],
                                      render_kw={'autofocus': True, 'placeholder': 'Password'})
    submit = SubmitField('Login')

class PaperForm(FlaskForm):
    author = StringField('Author', validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired()])
    journal = StringField('Journal')
    year = StringField('Year', validators=[DataRequired()])
    type = StringField('Type')
    doi = StringField('DOI')
    comments = TextAreaField('Additional information')
    keywords = TextAreaField('Keywords')
    abstract = TextAreaField('Abstract')
    license = StringField('Licence')
    url = StringField('Link to paper', validators=[])
    publisher = StringField('Publisher')
    ranking = StringField('Ranking')
    volume = StringField('Volume')
    file = FileField('File')
    arxiv = StringField('DOI')
    submit = SubmitField('Add Paper')
    add_to_favorites = SubmitField('Add to Favorites')


def get_users():
    return User.query.all()

def get_papers():
    return Paper.query.all()

class PRRForm(FlaskForm):
    date = DateField('Date of PRR', format='%Y-%m-%d', validators=[DataRequired()])
    presenter = SelectField('Paper Presenter', coerce=int, choices=[], validators=[DataRequired()])
    paper = SelectField('Paper', coerce=int, choices=[], validators=[DataRequired()])
    time = TimeField('Time', validators=[DataRequired()])
    room = StringField('Room', validators=[DataRequired()])
    submit = SubmitField('Create new PRR')

    def __init__(self, *args, **kwargs):
        super(PRRForm, self).__init__(*args, **kwargs)
        self.presenter.choices = [(user.id, user.username) for user in get_users()]
        self.paper.choices = [(paper.id, paper.title) for paper in get_papers()]

    def validate_date(self, field):
        try:
            # Attempt to parse the date; if successful, no action needed
            datetime.strptime(str(field.data), '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError('Invalid date format. Please use YYYY-MM-DD.')
