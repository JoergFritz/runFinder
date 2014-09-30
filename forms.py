from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, SelectField, HiddenField
from wtforms.validators import Required, Regexp
import re

class LoginForm(Form):
    address = TextField('address', validators = [Required()])
    condition = re.compile('(\d)+( \w+)?')
    distance = TextField('distance', validators = [Required(),Regexp(condition,message='Please reformat the distance you entered.')])

class ResultsForm(Form):
    weightProximity = HiddenField(validators = [Required()])
    weightPopularity = HiddenField(validators = [Required()])
    weightNature = HiddenField(validators = [Required()])
    weightAscent = HiddenField(validators = [Required()])
    weightOffroad = HiddenField(validators = [Required()])
    weightCircularity = HiddenField(validators = [Required()])
    userLat = HiddenField(validators = [Required()])
    userLng = HiddenField(validators = [Required()])
    runDist = HiddenField(validators = [Required()])


