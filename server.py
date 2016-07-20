from app import app, db, User, File, Folder
from flask import request, session, url_for, redirect,render_template, send_file, flash
from functools import wraps

from sqlalchemy.orm.exc import NoResultFound
from werkzeug.utils import secure_filename
import os
import shutil


ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mkv', 'mp4', 'mp3'])
SPACE_LIMIT = 1 * 1024 * 1024 * 1024
MAX_BANDWIDTH = 10 * 1024 * 1024 * 1024
MAX_FILE_SIZE = 10 * 1024 * 1024
MEDIA_DIR = app.config['UPLOAD_FOLDER']

def get_user(user_id):
    try:
        return db.session.query(User).filter(User.id==user_id).one()
    except:
        return not_found()

def get_folder(node_id):
    try:
        return db.session.query(Folder).filter(Folder.id==node_id).one()
    except:
        return not_found()

def get_file(file_id):
    try:
        return db.session.query(File).filter(File.id==file_id).one()
    except:
        return not_found()

def get_filesystem_filename(file_id,file_name):
    return str(file_id)+"_"+file_name

def is_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_logged_in',False):
            return redirect(url_for('login',next=request.url))
        return f(*args, **kwargs)
    return decorated

def authenticate(username, password):
    try:
        user = db.session.query(User).filter(User.username==username,User.password==password).one()
        session['id'] = user.id
        session['username'] = user.username
        session['is_logged_in'] = True
        return True
    except(Exception):
        return False


def delete_file(file_id,file_name):
    print("deleting:"+file_name)
    try:
        os.unlink(os.path.join(MEDIA_DIR,get_filesystem_filename(file_id,file_name)))
        db.session.query(File).filter(File.id==file_id).delete()
        db.session.commit()
    except:
        pass


def delete_folder_resursively(root):
    for i in root.files:
        delete_file(i.id,i.name)
    for i in root.sub_folders:
        delete_folder_resursively(i)
    db.session.query(Folder).filter(Folder.id==root.id).delete()
    db.session.commit()

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        if 'username' in request.form and 'password' in request.form:
            #TODO validate username and password
            try:
                u = db.session.query(User).filter(User.username==request.form['username']).one()
                flash("A user with the same username already exists in SSS","red")
            except:
                user = User(request.form['username'],request.form['password'])
                db.session.add(user)
                db.session.commit()
                registered_user = db.session.query(User).filter(User.username==request.form['username']).one()
                home_folder = Folder()
                home_folder.name = "home"
                home_folder.is_root = 1
                home_folder.user_id = registered_user.id
                db.session.add(home_folder)
                db.session.commit()
                flash("Successfully registered, please login..","green")
                return redirect(url_for("login"))
        else:
            flash("Invalid inputs","red")
    return render_template('register.html')


@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        if 'username' in request.form and 'password' in request.form and authenticate(request.form['username'], request.form['password']):
            if request.form.get("next", False):
                return redirect(request.form["next"]) #TODO validate this url before redirecting
            else:
                return redirect(url_for("index"))
        else:
            flash("Username or password is wrong","red")
    return render_template('login.html')

@app.route('/logout')
@requires_auth
def logout():
    # remove the username from the session if it's there
    session.pop('id', None)
    session.pop('user', None)
    session.pop('username', None)
    session.pop('is_logged_in', None)
    return redirect(url_for('index'))

@app.route('/')
@app.route('/index')
def index():
    if session.get('is_logged_in',False):
        try:
            root_id = db.session.query(Folder.id).filter(Folder.name=="home",Folder.is_root==1,Folder.user_id==session['id']).one().id
            return redirect("/node/"+str(root_id))
        except:
            return redirect(url_for("logout"))
    else:
        return render_template("home.html")


@app.route('/node/<int:node_id>',methods=['GET','POST'])
@requires_auth
def view_noed(node_id):
    user = get_user(session['id'])
    try:
        folder = get_folder(node_id)
    except NoResultFound:
        return not_found()

    if not folder.user_id == user.id:
        return unauthorised_error()

    if request.method == 'POST':
        if 'create_folder' in request.form and request.form['new_folder'] != None and request.form['new_folder'] != "":
            new_folder_name = request.form['new_folder']
            try:
                existing_folder = db.session.query(Folder).filter(Folder.parent == folder, Folder.name == new_folder_name).one()
                flash("A folder with same name already existing in this directory","yellow")
            except:
                new_folder = Folder()
                new_folder.name = request.form['new_folder']
                new_folder.parent = folder
                new_folder.user_id = user.id
                db.session.add(new_folder)
                db.session.commit()
                flash("Successfully created the folder","green")
        elif 'upload_file' in request.form and 'new_file' in request.files:
            new_file = request.files['new_file']
            new_file_name = secure_filename(new_file.filename)
            new_file.save(os.path.join("/tmp",new_file_name))
            new_file_size = os.stat(os.path.join("/tmp",new_file_name)).st_size
            used_bandwidth = user.bandwidth
            error = False
            if used_bandwidth > MAX_BANDWIDTH:
                error = True
                flash("There is no bandwidth left on your account","red")
            used_space = 0
            for file in user.files:
                used_space += int(file.size)
            if used_space+new_file_size > SPACE_LIMIT:
                error = True
                flash("There is no free space to upload this file","red")
            if new_file_size > MAX_FILE_SIZE:
                error = True
                flash("The file size is more than 2MB","red")
            if not is_allowed_file(new_file.filename):
                error = True
                flash("This type of file is not allowed to upload","red")
            if not error:
                try:
                    existing_file = db.session.query(File).filter(File.name == new_file_name,File.folder_id==folder.id, File.user_id == user.id).one()
                    shutil.copy(os.path.join("/tmp",new_file_name),os.path.join(MEDIA_DIR, get_filesystem_filename(existing_file.id,new_file_name)))
                except NoResultFound:
                    new_f = File()
                    new_f.name = secure_filename(new_file.filename)
                    new_f.user_id = user.id
                    new_f.folder_id = folder.id
                    new_f.size = new_file_size
                    user.bandwidth += new_file_size
                    db.session.add(new_f)
                    db.session.add(user)
                    db.session.commit()
                    shutil.copy(os.path.join("/tmp",new_file_name),os.path.join(MEDIA_DIR, get_filesystem_filename(new_f.id,new_file_name)))
                    #TODO if saving the fail fails, rollback the changes
                flash("Successfully uploaded the file","green")
        elif "delete_folder" in  request.form and "delete_folder_id" in request.form and request.form["delete_folder_id"] != "":
            delete_folder_id = request.form["delete_folder_id"]
            try:
                delete_folder = db.session.query(Folder).filter(Folder.id == delete_folder_id).one()
                if delete_folder.is_root == 1:
                    flash("Home folder can not be deleted","yellow")
                if delete_folder.user_id != user.id or delete_folder.parent_id != folder.id:
                    flash("You are not authorised to delete folder","red")
                    return unauthorised_error()
                delete_folder_resursively(delete_folder)
                flash("Successfully deleted the folder","green")
            except:
                flash("The folder you are trying to delete does not exist","red")
                return not_found()
        elif "delete_file" in  request.form and "delete_file_id" in request.form and request.form["delete_file_id"] != "":
            delete_file_id = request.form["delete_file_id"]
            try:
                file_to_delete = db.session.query(File).filter(File.id == delete_file_id).one()
                if file_to_delete.user_id != user.id or file_to_delete.folder_id != folder.id:
                    flash("You are not authorised to delete this file","red")
                    return unauthorised_error()
                delete_file(file_to_delete.id,file_to_delete.name)
                flash("Successfully deleted the file","green")
            except Exception as error:
                flash("The file you are trying to delete does not exist","red")
                return not_found()


    sub_folders = folder.sub_folders
    path = list()
    tmp = folder.parent
    while tmp != None:
        path.append((tmp.id,tmp.name))
        tmp = tmp.parent
    path.reverse()
    files = folder.files
    return render_template("view_dir.html",user=user, folder=folder, sub_folders=sub_folders, files=files,path=path)


@app.route('/download/<int:file_id>')
@requires_auth
def download(file_id):
    user = get_user(session['id'])
    try:
        file = get_file(file_id)
    except NoResultFound:
        return not_found()
    if not file.user_id == user.id:
        return unauthorised_error()
    return send_file(os.path.join(MEDIA_DIR, get_filesystem_filename(file.id,file.name)), as_attachment=True)


@app.errorhandler(401)
def unauthorised_error(error=None):
    status = 401
    if error == None:
        message = 'Unauthorised : ' + request.url
    else:
        message = error
    return render_template('error.html', status=status, message=message)

@app.errorhandler(404)
def not_found(error=None):
    status = 404
    if error == None:
        message = 'Not Found : ' + request.url
    else:
        message = error
    return render_template('error.html', status=status, message=message)

@app.errorhandler(500)
def internal_server_error(error=None):
    status = 500
    if error == None:
        message = 'Internal Server Error : ' + request.url
    else:
        message = error
    return render_template('error.html', status=status, message=message)




