from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, SelectField
from wtforms.validators import Required

class LoginForm(Form):
    address = TextField('city', validators = [Required()])
    distance = TextField('distance', validators = [Required()])

class ResultsForm(Form):
    address = TextField('city', validators = [Required()])

