from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, SelectField, HiddenField
from wtforms.validators import Required, Regexp
import re

class LoginForm(Form):
    address = TextField('address', validators = [Required()])
    condition = re.compile('(\d)+( \w+)?')
    distance = TextField('distance', validators = [Required(),Regexp(condition,message='Please reformat the distance you entered.')])

class ResultsForm(Form):
    weightProximity = HiddenField()
    weightPopularity = HiddenField()
    weightNature = HiddenField()
    weightAscent = HiddenField()
    weightOffroad = HiddenField()
    weightCircularity = HiddenField()
    userLat = HiddenField()
    userLng = HiddenField()
    runDist = HiddenField()

class DownloadForm(Form):
    downId = HiddenField(validators = [Required()])


