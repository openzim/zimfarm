import app
from routes import task


app.flask.route("/")(task.hello)
app.flask.route("/task/delayed_add", methods=['POST'])(task.delayed_add)
app.flask.route("/task/status/<string:id>", methods=['GET', 'POST'])(task.status)
app.flask.route("/tasks", methods=['GET'])(task.get_tasks)


if __name__ == "__main__":
    app.flask.run(host='0.0.0.0', debug=True, port=80)