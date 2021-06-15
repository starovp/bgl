from flask import render_template, request, flash, redirect, url_for
from app import app, db
from app.forms import EditProfileForm, LoginForm, RegistrationForm, SubmitMatchForm, PowerGridScore, FieldList, FormField
from app.game_forms import *
from app.models import User, Match, Game
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from wtforms.validators import DataRequired, ValidationError

import sys
import json
import math

from sqlalchemy.orm.attributes import flag_modified


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
    scoreformname = game.display_name.replace(' ', '') + 'Score'
    baseformname = game.display_name.replace(' ', '') + 'Form'
    victoryname = game.display_name.replace(' ', '') + 'Victory'

    current_mod = sys.modules[__name__]

    score_form = getattr(current_mod, scoreformname)
    base_form = getattr(current_mod, baseformname)
    victory_check = getattr(current_mod, victoryname)

    class LocalForm(score_form):pass
    LocalForm.scores = FieldList(FormField(base_form), min_entries=int(entries), max_entries=game.max_players)
    form = LocalForm()

    if request.method == 'POST':
        scores = form.data['scores']
        for ele in scores:
            ele.pop('csrf_token', None)
            for sub in ele:
                try:
                    ele[sub] = int(ele[sub])
                except:
                    pass

        final_scores = victory_check(scores)
        pre_winner = final_scores[0]['player']
        final_winner = User.query.filter_by(displayname=pre_winner).first_or_404()
        ranks = update_ranks(final_scores, game)
        for ele in ranks:
            for sub in final_scores:
                if sub['player'] == ele[0]:
                    sub['previous_mmr'] = ele[1]
                    sub['mmr_change'] = ele[2]
                    sub['new_mmr'] = ele[1] + ele[2]

        match = Match(game=game.id, stats=final_scores, winner=final_winner.id)
        db.session.add(match)
        db.session.commit()
        flash('Match Recorded!')

        return redirect(url_for('matches'))

    return render_template('addmatch.html', title='Add Match', game=game, form=form, range=range, entries=int(entries))


def elo_expected(p1, p2):
    return 1/(1+10**((p2-p1)/400))

def elo_new(prev, expected, score):
    k = 32
    return prev + (k * (score-expected))

def update_ranks(scores, game):
    game_field = game.main_score_field
    p_list = []
    highest_mmr = 0
    for ele in scores:
        player_name = ele['player']
        player = User.query.filter_by(displayname=player_name).first_or_404()
        player_mmr = player.game_mmr
        player_score = ele[game_field]
        if player_mmr is None:
            player.game_mmr = {}
            flag_modified(player, 'game_mmr')
            db.session.commit()
        player_mmr = player.game_mmr
        if game.gname not in player_mmr:
            player_mmr[game.gname] = 1500
            flag_modified(player, 'game_mmr')
            db.session.commit()
        player_mmr = player.game_mmr
        if player_mmr[game.gname] > highest_mmr:
            highest_mmr = player_mmr[game.gname]
        p_list.append([player_name, int(player_mmr[game.gname]), int(player_score)])

    scores = []
    new_mmrs = []
    for ele in p_list:
        temp_mmr = []
        pos = p_list.index(ele)
        for sub in [g for g in p_list if g != ele]:
            sub_pos = p_list.index(sub)
            exp = elo_expected(ele[1], sub[1])

            if pos < sub_pos:
                final_pos = 1
            elif pos > sub_pos:
                final_pos = 0

            nelo = elo_new(ele[1], exp, final_pos)
            temp_mmr.append(nelo-ele[1])
        
        scores.append(int(ele[2]))
        
        avg_range = sum(temp_mmr)/len(temp_mmr)
        new_mmrs.append([ele[0], ele[1], avg_range])
    
    avg_score = sum(scores)/len(scores)
    stdevs = []
    for ele in p_list:
        stdevs.append((ele[2]-avg_score)**2)

    mmrs = []
    for ele in new_mmrs:
        mmrs.append(ele[1])
    
    avg_mmr = sum(mmrs)/len(mmrs)
    mmr_devs = []
    for ele in new_mmrs:
        mmr_devs.append((avg_mmr-ele[1])**2)

    adjustment = math.log(1+math.sqrt(sum(stdevs)/len(stdevs)))

    for ct, ele in enumerate(new_mmrs):
        ele[2] = ele[2]*adjustment
    
    for ele in new_mmrs:
        player = User.query.filter_by(displayname=ele[0]).first_or_404()
        score_dict = player.game_mmr
        score_dict[game.gname] = round(ele[1]+ele[2])
        player.game_mmr = score_dict
        flag_modified(player, 'game_mmr')
        db.session.commit()

    return new_mmrs
    

@app.route('/matches')
@login_required
def matches():
    matches = Match.query.all()
    return render_template('matches.html', title='Matches', matches=matches, list=list)


@app.route('/match/<matchid>')
@login_required
def match(matchid):
    match = Match.query.filter_by(id=matchid).first_or_404()
    return render_template('match.html', match=match)
