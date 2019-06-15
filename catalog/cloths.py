from flask import Flask, render_template, request
from flask import redirect, url_for, jsonify, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Cloth, Base, Model, User
from flask import session as login_session
import random
import string
import json

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Cloths item-catalog"
engine = create_engine(
    'sqlite:///clothsdata.db', connect_args={'check_same_thread': False},
    echo=True)
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# FOR USER LOGIN PURPOSE
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current state is %s" %login_session['state']
    cloth = session.query(Cloth).all()
    model = session.query(Model).all()
    return render_template('login.html', STATE=state, cloth=cloth,
                           model=model)


# IF USER ALREADY LOGGED IN
@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid State parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data

    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
                                 json.dumps(
                                            'Current user already connected'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<center><h2><font color="green">Welcome '
    output += login_session['username']
    output += '!</font></h2></center>'
    output += '<center><img src="'
    output += login_session['picture']
    output += ' " style = "width: 200px; -webkit-border-radius: 200px;" '
    output += ' " style = "height: 200px;border-radius: 200px;" '
    output += ' " style = "-moz-border-radius: 200px;"></center>" '
    flash("you are now logged in as %s" % login_session['username'])
    print("Done")
    return output


# CREATING NEW USER LOGIN
def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()

    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


# FOR GETTING USER INFORMATION
def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


# FOR GETTING USER EMAIL ADDRESS
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except Exception as e:
        return None


# FOR READING CLOTH JSON DATA FROM WEB BROWSER
@app.route('/cloth/JSON')
def clothJSON():
    cloth = session.query(Cloth).all()
    return jsonify(cloth=[c.serialize for c in cloth])


# # FOR READING CLOTH WISE MODEL JSON
@app.route('/cloth/<int:cloth_id>/menu/<int:model_id>/JSON')
def clothListJSON(cloth_id, model_id):
    Model_List = session.query(Model).filter_by(id=model_id).one()
    return jsonify(Model_List=Model_List.serialize)


# TO READ MODEL JSON DATA
@app.route('/cloth/<int:model_id>/menu/JSON')
def modelListJSON(model_id):
    cloth = session.query(Cloth).filter_by(id=model_id).one()
    model = session.query(Model).filter_by(model_id=model.id).all()
    return jsonify(Model_Lists=[i.serialize for i in model])


# HOME PAGE FOR ENTAIRE PROJECT
@app.route('/cloth/')
def showCloth():
    cloth = session.query(Cloth).all()
    return render_template('cloth.html', cloth=cloth)

# TO CREATE NEW CLOTH
@app.route('/cloth/new/', methods=['GET', 'POST'])
def newCloth():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCloth = Cloth(name=request.form['name'],
                             user_id=login_session['user_id'])
        session.add(newCloth)
        session.commit()
        return redirect(url_for('showCloth'))
    else:
        return render_template('newCloth.html')


# FOR EDITING EXCISTING CLOTH NAME
@app.route('/cloth/<int:cloth_id>/edit/', methods=['GET', 'POST'])
def editCloth(cloth_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedCloth = session.query(Cloth).filter_by(id=cloth_id).one()
    creater_id = getUserInfo(editedCloth.user_id)
    user_id = getUserInfo(login_session['user_id'])
    if creater_id.id != login_session['user_id']:
        flash("You cannot edit this Cloth "
              "This is belongs to %s" % (creater_id.name))
        return redirect(url_for('showCloth'))
    if request.method == 'POST':
        if request.form['name']:
            editedCloth.name = request.form['name']
            flash("Country Successfully Edited %s" % (editedCloth.name))
            return redirect(url_for('showCloth'))
    else:
        return render_template('editCloth.html', cloth=editedCloth)


# FOR DELETING EXCISTING CLOTH
@app.route('/cloth/<int:cloth_id>/delete/', methods=['GET', 'POST'])
def deleteCloth(cloth_id):
    if 'username' not in login_session:
        return redirect('/login')
    clothToDelete = session.query(Cloth).filter_by(id=cloth_id).one()
    creater_id = getUserInfo(clothToDelete.user_id)
    user_id = getUserInfo(login_session['user_id'])
    if creater_id.id != login_session['user_id']:
        flash("You cannot delete this Country "
              "This is belongs to %s" % (creater_id.name))
        return redirect(url_for('showCloth'))
    if request.method == 'POST':
        session.delete(clothToDelete)
        flash("Successfully Deleted %s" % (clothToDelete.name))
        session.commit()
        return redirect(url_for('showCloth', cloth_id=cloth_id))
    else:
        return render_template('deleteCloth.html', cloth=clothToDelete)


# THIS IS FOR DISPLAYING TOTAL MODEL LISTS
@app.route('/cloth/<int:cloth_id>/models')
def showModels(cloth_id):
    cloth = session.query(Cloth).filter_by(id=cloth_id).one()
    model = session.query(Model).filter_by(model_id=cloth_id).all()
    return render_template('menu.html', cloth=cloth, model=model)


# CREATING NEW MODEL
@app.route('/cloth/<int:model_id>/new/', methods=['GET', 'POST'])
def newModelList(model_id):
    if 'username' not in login_session:
        return redirect('login')
    cloth = session.query(Cloth).filter_by(id=model_id).one()
    creater_id = getUserInfo(cloth.user_id)
    user_id = getUserInfo(login_session['user_id'])
    if creater_id.id != login_session['user_id']:
        flash("You cannot add this player "
              "This is belongs to %s" % (creater_id.name))
        return redirect(url_for('showCloth', cloth_id=model_id))
    if request.method == 'POST':
        newList = Model(name=request.form['name'],
                         price=request.form['price'],
                         color=request.form['color'],
                         pic=request.form['pic'],
                         brand=request.form['brand'],
                         model_id=model_id,
                         user_id=login_session['user_id'])
        session.add(newList)
        session.commit()
        flash("New Player List %s is created" % (newList))
        return redirect(url_for('showModels', cloth_id=model_id))
    else:
        return render_template('newmodellist.html', model_id=model_id)


# FOR EDITING PERTICULAR MODEL
@app.route('/cloth/<int:cloth_id>/<int:m_id>/edit/',
           methods=['GET', 'POST'])
def editModelList(cloth_id, m_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedList = session.query(Model).filter_by(id=m_id).one()
    cloth = session.query(Cloth).filter_by(id=cloth_id).one()
    creater_id = getUserInfo(editedList.user_id)
    user_id = getUserInfo(login_session['user_id'])
    if creater_id.id != login_session['user_id']:
        flash("You cannot edit this Country "
              "This is belongs to %s" % (creater_id.name))
        return redirect(url_for('showModels', cloth_id=cloth_id))
    if request.method == 'POST':
        editedList.name = request.form['name']
        editedList.price = request.form['price']
        editedList.color = request.form['color']
        editedList.pic = request.form['pic']
        editedList.brand = request.form['brand']
        session.add(editedList)
        session.commit()
        flash("Model List has been edited!!")
        return redirect(url_for('showModels', cloth_id=cloth_id))
    else:
        return render_template('editmodellist.html',
                               cloth=cloth, model=editedList)


# FOR DELETING PERTICULAR MODEL
@app.route('/cloth/<int:model_id>/<int:list_id>/delete/',
           methods=['GET', 'POST'])
def deleteModelList(model_id, list_id):
    if 'username' not in login_session:
        return redirect('/login')
    cloth = session.query(Cloth).filter_by(id=model_id).one()
    listToDelete = session.query(Model).filter_by(id=list_id).one()
    creater_id = getUserInfo(listToDelete.user_id)
    user_id = getUserInfo(login_session['user_id'])
    if creater_id.id != login_session['user_id']:
        flash("You cannot delete this Country "
              "This is belongs to %s" % (creater_id.name))
        return redirect(url_for('showModels', cloth_id=model_id))
    if request.method == 'POST':
        session.delete(listToDelete)
        session.commit()
        flash("Player list has been Deleted!!!")
        return redirect(url_for('showModels', cloth_id=model_id))
    else:
        return render_template('deletemodellist.html', lists=listToDelete)


# IT IS FOR LOGOUT FROM THE APPLICATION
@app.route('/disconnect')
def logout():
    access_token = login_session['access_token']
    print("In gdisconnect access token is %s", access_token)
    print("User Name is:")
    print(login_session['username'])

    if access_token is None:
        print("Access Token is None")
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = login_session['access_token']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = \
        h.request(uri=url, method='POST', body=None,
                  headers={'content-type':
                           'application/x-www-form-urlencoded'})[0]

    print result['status']
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash("Successfully logged out")
        return redirect(url_for('showCloth'))
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
