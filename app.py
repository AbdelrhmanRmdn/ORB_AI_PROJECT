from __future__ import annotations

from flask import Flask

from database.database_manager import DatabaseManager


app = Flask(__name__)


@app.route("/")
def index() -> str:
    database = DatabaseManager()
    health = database.health_check()
    users = database.get_authorized_users()
    user_items = "".join(f"<li>{user.name}</li>" for user in users)
    if not user_items:
        user_items = "<li>No authorized users returned.</li>"
    return (
        "<h1>ORB AI Assistant</h1>"
        f"<p>Database: {health.message}</p>"
        "<h2>Authorized Users</h2>"
        f"<ul>{user_items}</ul>"
    )


if __name__ == "__main__":
    app.run(debug=True)
