from app import app,db
from app.models import  Folder,User,File
import os

# if os.path.exists("./app.db"):
#     os.unlink("./app.db")



# db.create_all()
#
#
# u = User("asdf","asdfasdfasdf")
# db.session.add(u)
# db.session.commit()
#
# user = db.session.query(User).filter(User.username=="asdf")[0]
#
#
#
#
# f = Folder()
# f.name = "root_"+user.username
# f.user_id = user.id
# f.is_root = True


folder = db.session.query(Folder).filter(Folder.id==1)[0]

# f = Folder()
# f.name = "root_"+user.username
# f.user_id = user.id
# f.is_root = True

user = db.session.query(User).filter(User.username=="asdf")[0]


# for i in folder.files:
#     print(i.name)


for i in folder.sub_folders:
    print(i.name)
