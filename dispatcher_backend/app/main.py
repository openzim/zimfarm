import app
from routes import auth, task

## init
from database.models import User
from werkzeug.security import generate_password_hash
if User.query.filter_by(username='chris').first() is None:
    app.db.session.add(User(username='chris', password_hash=generate_password_hash('password')))
    app.db.session.add(User(username='kelson42', password_hash=generate_password_hash('password')))
    app.db.session.commit()


app.flask.route("/auth/login", methods=['POST'])(auth.login)
app.flask.route("/task/enqueue/zimfarm_generic", methods=['POST'])(task.enqueue_zimfarm_generic)
app.flask.route("/task/<string:id>", methods=['GET', 'POST'])(task.task_detail)
app.flask.route("/task/list", methods=['GET'])(task.list_tasks)


if __name__ == "__main__":
    app.flask.run(host='0.0.0.0', debug=True, port=80)