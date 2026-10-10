import os

from flask import Flask, abort, jsonify, request, send_from_directory

from backend import models

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
PAGES = {"find", "register", "dashboard", "track"}

app = Flask(__name__, static_folder=None)


# ---------- frontend pages ----------
@app.get("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/styles.css")
def styles():
    return send_from_directory(FRONTEND_DIR, "styles.css")


@app.get("/common.js")
def common_js():
    return send_from_directory(FRONTEND_DIR, "common.js")


@app.get("/<page>")
def page(page):
    if page not in PAGES:
        abort(404)
    return send_from_directory(FRONTEND_DIR, page + ".html")


# ---------- API ----------
@app.post("/api/donors")
def register_donor():
    return jsonify(models.register_donor(request.get_json(silent=True) or {})), 201


@app.get("/api/search")
def search():
    return jsonify(models.search_donors(request.args.get("blood_group"), request.args.get("city")))


@app.post("/api/requests")
def create_request():
    return jsonify(models.create_request(request.get_json(silent=True) or {})), 201


@app.get("/api/requests/<int:request_id>")
def request_status(request_id):
    return jsonify(models.request_status(request_id, request.args.get("code")))


@app.get("/api/donors/<int:donor_id>/requests")
def donor_requests(donor_id):
    return jsonify(models.donor_requests(donor_id, request.args.get("code")))


@app.post("/api/donors/<int:donor_id>/requests/<int:request_id>")
def respond(donor_id, request_id):
    body = request.get_json(silent=True) or {}
    return jsonify(models.respond_to_request(donor_id, body.get("code"), request_id, body.get("action")))


@app.post("/api/donors/<int:donor_id>/availability")
def availability(donor_id):
    body = request.get_json(silent=True) or {}
    return jsonify(models.set_availability(donor_id, body.get("code"), body.get("available")))
@app.get("/api/stats")
def stats():
    return jsonify(models.get_stats())

# ---------- errors ----------
@app.errorhandler(models.ValidationError)
def bad_input(err):
    return jsonify(error=str(err)), 400


@app.errorhandler(models.AuthError)
def forbidden(err):
    return jsonify(error=str(err)), 403


if __name__ == "__main__":
    app.run(debug=True)
