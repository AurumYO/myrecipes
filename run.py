
from flask_migrate import Migrate
from recblog import create_app, db
from recblog.models import User, Follow, Role, Permission, Post, Comment

app = create_app()

migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Follow=Follow, Role=Role,
                Permission=Permission, Post=Post, Comment=Comment)

if __name__ == '__main__':
    app.run(debug=True)
