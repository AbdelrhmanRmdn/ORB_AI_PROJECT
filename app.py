from __future__ import annotations

from html import escape

from flask import Flask

from database.database_manager import DatabaseManager
from database.queries import COMMAND_LOGS_TABLE
from database.supabase_client import create_supabase_client


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


@app.route("/todos")
@app.route("/command-logs")
def command_logs() -> tuple[str, int] | str:
    supabase = create_supabase_client()
    if supabase is None:
        return "<h1>Command Logs</h1><p>Supabase is not configured.</p>", 503

    try:
        response = (
            supabase.table(COMMAND_LOGS_TABLE)
            .select("created_at,raw_command,detected-intent,response_text,status")
            .limit(20)
            .execute()
        )
    except Exception as exc:
        return f"<h1>Command Logs</h1><p>Could not fetch logs: {escape(str(exc))}</p>", 502

    log_items = "".join(
        "<li>"
        f"{escape(str(log.get('raw_command', '')))} "
        f"({escape(str(log.get('detected-intent', log.get('detected_intent', 'unknown'))))}): "
        f"{escape(str(log.get('response_text', '')))} "
        f"[{escape(str(log.get('status', '')))}]"
        "</li>"
        for log in response.data or []
    )
    if not log_items:
        log_items = "<li>No command logs returned.</li>"
    return f"<h1>Command Logs</h1><ul>{log_items}</ul>"


if __name__ == "__main__":
    app.run(debug=True)
