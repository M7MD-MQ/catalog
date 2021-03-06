#! /usr/bin/env python
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    jsonify,
    url_for,
    flash
)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from genre_setup import Base, Genre, Movie, User
from sqlalchemy.pool import SingletonThreadPool
from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests


app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "MoviesCatalog"

engine = create_engine('sqlite:///movies.db?check_same_thread=False',
                       poolclass=SingletonThreadPool)
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is'
                                 + 'already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if a user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px;'\
              'height: 300px;'\
              'border-radius: 150px;'\
              '-webkit-border-radius: 150px;'\
              '-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except NoResultFound:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('showAllGenre'))

    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view Genre Information
@app.route('/genre/<int:genre_id>/movie/JSON')
def genreMenuJSON(genre_id):
    genre = session.query(Genre).filter_by(id=genre_id).one()
    items = session.query(Movie).filter_by(
        genre_id=genre_id).all()
    return jsonify(Movies=[i.serialize for i in items])


@app.route('/genre/<int:genre_id>/movie/<int:movie_id>/JSON')
def movieItemJSON(genre_id, movie_id):
    Movie_Details = session.query(Movie).filter_by(id=movie_id).one()
    return jsonify(Movie_Details=Movie_Details.serialize)


@app.route('/genre/JSON')
def genresJSON():
    genres = session.query(Genre).all()
    return jsonify(genres=[r.serialize for r in genres])


# Main Route Has All Genres
@app.route('/')
@app.route('/genre/')
def showAllGenre():
    list = session.query(Genre).all()
    return render_template('allGenreList.html', list=list)


# Genre details page
@app.route('/Genre/<int:genre_id>', methods=['GET', 'POST'])
def showGenre(genre_id):
    genre = session.query(Genre).filter_by(id=genre_id).one()
    movie = session.query(Movie).filter_by(genre_id=genre_id).all()
    if request.method == 'POST':
        newMovie = Movie(name=request.form['name'],
                         bio=request.form['bio'], genre_id=genre_id,
                         user_id=getUserID(login_session['email']))
        session.add(newMovie)
        session.commit()
        flash("New movie has been added")
        return redirect(url_for('showGenre', genre_id=genre_id))
    else:
        if 'username' in login_session:
            return render_template('genre.html', genre=genre, movie=movie)
        else:
            return render_template('publicgenre.html', genre=genre,
                                   movie=movie)


# Movie Edit Page
@app.route('/Genre/<int:genre_id>/<int:movie_id>/edit',
           methods=['GET', 'POST'])
def editMovie(genre_id, movie_id):
    editMovie = session.query(Movie).filter_by(id=movie_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        if getUserID(login_session['email']) != int(editMovie.user_id):
            flash("Sorry, You Are Not Authorized To Edit This Movie!")
            return redirect(url_for('showGenre', genre_id=genre_id))
        if request.form['name']:
            editMovie.name = request.form['name']
        if request.form['bio']:
            editMovie.bio = request.form['bio']
            session.add(editMovie)
            session.commit()
        flash("Movie info have been updated")
        return redirect(url_for('showGenre', genre_id=genre_id))
    else:
        return render_template('genre.html', genre=genre, movie=movie)


# Movie Delete Page
@app.route('/Genre/<int:genre_id>/<int:movie_id>/delete',
           methods=['GET', 'POST'])
def deleteMovie(genre_id, movie_id):
    movieToBeDeleted = session.query(Movie).filter_by(id=movie_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        if getUserID(login_session['email']) != int(movieToBeDeleted.user_id):
            flash("Sorry, You Are Not Authorized To Delet This Movie!")
            return redirect(url_for('showGenre', genre_id=genre_id))
        session.delete(movieToBeDeleted)
        session.commit()
        flash("Movie has been deleted")
        return redirect(url_for('showGenre', genre_id=genre_id))
    else:
        return render_template('genre.html', genre=genre, movie=movie)


# Main part runs if there is no exceptions, from python interpretur
if __name__ == '__main__':
    app.secret_key = 'super_secure'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
