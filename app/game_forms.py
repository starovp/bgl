from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError

class PowerGridForm(FlaskForm):
    player = StringField('Player', validators=[DataRequired()])
    plants = StringField('Plants', validators=[DataRequired()])
    money = StringField('Money', validators=[DataRequired()])

def PowerGridVictory(scores):
    fields = ['money', 'plants']
    for field in fields:
        scores = sorted(
            scores, 
            key=lambda i: (
                i[f'{field}']
            ),
            reverse=True
        )
    return scores