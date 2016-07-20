from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.debug = True
app.config.from_object('config')
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'  #TODO move this to secure location
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), unique=True)
    password = db.Column(db.String(128)) # TODO encrypt this
    is_active = db.Column(db.Boolean, default=True)
    bandwidth = db.Column(db.Integer, default=0)

    files = db.relationship("File",backref='user', lazy='dynamic')
    folders = db.relationship("Folder",backref='user',lazy='dynamic')

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return '<User %r>' % self.username


class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(512))
    size = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'))

    def __repr__(self):
        return '<File %r>' % self.name,self.size

class Folder(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(512))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_root = db.Column(db.Boolean, default=False)
    files = db.relationship("File", backref='folder', lazy='dynamic')
    parent_id = db.Column(db.Integer,db.ForeignKey('folder.id'))
    parent = db.relationship(lambda: Folder, remote_side=id, backref='sub_folders')


    def __repr__(self):
        return '<Folder %r>' % self.name



db.create_all()
db.session.commit()

