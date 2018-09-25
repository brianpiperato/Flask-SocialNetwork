from flask import Flask, render_template,request,redirect,url_for
from sqlalchemy import create_engine
from flask_sqlalchemy import SQLAlchemy
from snowflake.sqlalchemy import URL
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required
from flask_login import current_user
from flask_mail import Mail
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView


USERNAME = "bpiperato"
PASSWORD = "Patricia12"
ACCOUNT = "mx86048.us-east-1"
SCHEMA = "PUBLIC"
WAREHOUSE = "BP_WAREHOUSE"
DATABASE = "FLASK_SOCIAL"


application = Flask(__name__)
admin = Admin(application)
application.config['SQLALCHEMY_DATABASE_URI'] = 'snowflake://{user}:{password}@{account}/{database}/{schema}'.format(
    user=USERNAME,
    password=PASSWORD,
    account=ACCOUNT,
    database=DATABASE,
    schema = SCHEMA
)
application.config['SECRET_KEY'] = 'super-secret'
application.config['SECURITY_REGISTERABLE'] = True
application.config['SECURITY_PASSWORD_HASH'] = 'bcrypt'
application.config['SECURITY_PASSWORD_SALT'] = '$2a$16$PnnIgfMwkOjGX4SkHqSOPO'
application.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 25,
    MAIL_USE_TLS = False,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = 'gmail_username',
    MAIL_PASSWORD = 'gmail_password'
)
application.debug = True
db = SQLAlchemy(application)


# Define models

roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), db.Sequence('id_seq'), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, db.Sequence('id_seq'), primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

class Post(db.Model):
    id = db.Column(db.Integer, db.Sequence('id_seq'), primary_key = True)
    post_content = db.Column(db.String(200))
    posted_by = db.Column(db.String(100))


    def __init__(self,post_content,posted_by):
        self.post_content = post_content
        self.posted_by = posted_by

    def __respr__(self):
        return '<Post:  %r>' % self.post_content

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(application, user_datastore)


class UserDetails(db.Model):
    id = db.Column(db.Integer, db.Sequence('id_seq'), primary_key = True)
    user_id = db.Column(db.Integer)
    username = db.Column(db.String(100))
    profile_pic = db.Column(db.String(300))
    location = db.Column(db.String(100))

    def __init__ (self,user_id,username,profile_pic,location):
        self.user_id = user_id
        self.username = username
        self.profile_pic = profile_pic
        self.location = location

    def __repr__(self):
        return '<UserDetails %r>' % self.username


class MyModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self):
        return 'hi'

'''
class MyAdminView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated
'''


admin.add_view(MyModelView(User, db.session))
admin.add_view(MyModelView(Post, db.session))

#VIEWS
@application.route('/')
@login_required
def index():
    singlepost = Post.query.all()
    userD = UserDetails.query.all()
    return render_template('feed2.html', singlepost = singlepost, userD = userD)


@application.route('/posting')
@login_required
def posting():
    live_user = User.query.filter_by(email = current_user.email).first()
    return render_template('add_post.html', live_user = live_user)

@application.route('/add_post', methods=['POST'])
def add_post():
    post = Post(request.form['pcontent'], request.form['pemail'])
    db.session.add(post)
    db.session.commit()
    return redirect(url_for('index'))

@application.route('/user_list')
@login_required
def get_user_list():
    users = User.query.all()
    userD = UserDetails.query.all()
    return render_template('user_list.html', users = users, userD = userD)


@application.route('/feed2')
@login_required
def get_feed():
    singlepost = Post.query.all()
    userD = UserDetails.query.all()
    return render_template('feed2.html', singlepost = singlepost, userD = userD)


@application.route('/editprofile')
@login_required
def edit_profile():
    live_user = User.query.filter_by(email = current_user.email).first()
    return render_template('user_detail.html', live_user = live_user)

@application.route('/add_user_details',methods=['POST'])
def add_user_details():
    user_details = UserDetails(request.form['pid'], request.form['username'], request.form['profile_pic'], request.form['location'])
    db.session.add(user_details)
    db.session.commit()
    return redirect(url_for('index'))


@application.route('/profile/<user_id>')
def user_profile(user_id):
    oneUser = UserDetails.query.filter_by(user_id = user_id).first()
    sUser = User.query.filter_by(id = oneUser.user_id).first()
    user_posts = Post.query.filter_by(posted_by = sUser.email)
    return render_template('user_profile.html', oneUser = oneUser, sUser = sUser, user_posts = user_posts)

if __name__ == "__main__":
    application.run(debug=True)
