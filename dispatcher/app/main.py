import app
from routes import task


app.flask.route("/")(task.hello)
app.flask.route("/task/enqueue/delayed_add", methods=['POST'])(task.delayed_add)
app.flask.route("/task/enqueue/subprocess", methods=['POST'])(task.subprocess)
app.flask.route("/task/<string:id>", methods=['GET', 'POST'])(task.task)
app.flask.route("/task", methods=['GET'])(task.tasks)


if __name__ == "__main__":
    app.flask.run(host='0.0.0.0', debug=True, port=80)