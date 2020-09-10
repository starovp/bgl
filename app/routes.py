from flask import render_template, request, flash, redirect, url_for
from app import app, db
from app.forms import EditProfileForm, LoginForm, RegistrationForm, SubmitMatchForm, PowerGridScore, PowerGridForm, FieldList, FormField
from app.models import User, Match, Game
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
import sys
import json

@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html', title='Home')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, displayname=form.displayname.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<displayname>')
@login_required
def user(displayname):
    user = User.query.filter_by(displayname=displayname).first_or_404()
    posts = [
        {'author': user, 'body':'Test post 1'},
        {'author': user, 'body':'Test post 2'}
    ]
    matches = [
        {'game': 'GWT', 'winner': 'ivan', 'skill': 'high', 'timestamp':'NYE'}
    ]
    return render_template('user.html', user=user, posts=posts, matches=matches)

@app.route('/edit_profile', methods=['GET','POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.displayname)
    if form.validate_on_submit():
        current_user.displayname = form.displayname.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.displayname.data = current_user.displayname
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)

@app.route('/games')
@login_required
def games():
    games = Game.query.all()
    return render_template('games.html', title='Add Match', games=games)

@app.route('/addmatch/<game>/<entries>', methods=['GET', 'POST'])
@login_required
def addmatch(game, entries):
    game = Game.query.filter_by(gname=game).first()
    scoreformname = game.gname.replace(' ','')+'Score'
    baseformname = game.gname.replace(' ','')+'Form'
    current_mod = sys.modules[__name__]
    score_form = getattr(current_mod, scoreformname)
    base_form = getattr(current_mod, baseformname)
    class LocalForm(score_form):pass
    LocalForm.scores = FieldList(FormField(base_form), min_entries=int(entries), max_entries=6)
    form = LocalForm()
    if form.submit():
        scores = form.data['scores']
        for ele in scores:
            ele.pop('csrf_token', None)
        scores = json.dumps(scores)
        match = Match(game=game.id, stats=scores)
        flash('Match Recorded!')
        return redirect(url_for('matches'))
    return render_template('addmatch.html', title='Add Match', game=game, form=form)

@app.route('/matches')
@login_required
def matches():
    matches = Match.query.all()
    return render_template('matches.html', title='Matches', matches=matches)

@app.route('/match/<matchid>')
@login_required
def match(matchid):
    match = Match.query.filter_by(id=matchid).first_or_404()
    return render_template('match.html', match=match)
