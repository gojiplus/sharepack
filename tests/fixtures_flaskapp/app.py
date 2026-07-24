"""Clipnotes: a tiny snippet ledger used as sharepack's Flask fixture."""
import sqlite3

from flask import Flask, abort, flash, g, redirect, render_template, request

app = Flask(__name__)
app.secret_key = "clipnotes-demo-not-a-secret"

DB = "clips.sqlite3"


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        if title:
            db().execute(
                "INSERT INTO clips (title, body) VALUES (?, ?)", (title, body)
            )
            db().commit()
            flash(f"saved “{title}”")
        return redirect("/")
    rows = db().execute("SELECT * FROM clips ORDER BY id DESC").fetchall()
    return render_template("index.html", clips=rows)


@app.route("/clip/<int:clip_id>")
def detail(clip_id):
    row = db().execute("SELECT * FROM clips WHERE id = ?", (clip_id,)).fetchone()
    if row is None:
        abort(404)
    return render_template("detail.html", clip=row)


@app.route("/about")
def about():
    return render_template("about.html")
