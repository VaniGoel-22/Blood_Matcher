import re
import secrets

from database import get_db

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
URGENCY_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

# recipient group -> donor groups they can safely receive from
CAN_RECEIVE_FROM = {
    "A+": ["A+", "A-", "O+", "O-"],
    "A-": ["A-", "O-"],
    "B+": ["B+", "B-", "O+", "O-"],
    "B-": ["B-", "O-"],
    "AB+": list(BLOOD_GROUPS),          # universal recipient
    "AB-": ["AB-", "A-", "B-", "O-"],
    "O+": ["O+", "O-"],
    "O-": ["O-"],                       # can only receive O-
}

PHONE_RE = re.compile(r"^\+?[0-9][0-9\s-]{6,14}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ValidationError(Exception):
    """Bad input -> HTTP 400."""


class AuthError(Exception):
    """Wrong or missing token -> HTTP 403."""


def _clean(value):
    return (value or "").strip() if isinstance(value, str) else ""


def _group(value):
    g = _clean(value).upper()
    if g not in BLOOD_GROUPS:
        raise ValidationError("Choose a valid blood group.")
    return g


def _int(value, label):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{label} must be a number.")


def _check_token(stored, given):
    if not given or not secrets.compare_digest(stored, str(given)):
        raise AuthError("Wrong ID or access code.")


# ---------------- donors ----------------
def register_donor(data):
    name, city = _clean(data.get("name")), _clean(data.get("city"))
    phone, email = _clean(data.get("phone")), _clean(data.get("email"))
    group = _group(data.get("blood_group"))
    if len(name) < 2 or len(city) < 2:
        raise ValidationError("Enter your name and city.")
    if not PHONE_RE.match(phone):
        raise ValidationError("Enter a valid phone number.")
    if not EMAIL_RE.match(email):
        raise ValidationError("Enter a valid email address.")
    available = 1 if data.get("is_available", True) else 0
    token = secrets.token_urlsafe(8)
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO donors (name, blood_group, city, phone, email, token, is_available) "
            "VALUES (?,?,?,?,?,?,?)",
            (name, group, city, phone, email, token, available),
        )
        return {"donor_id": cur.lastrowid, "access_code": token}


def search_donors(blood_group, city):
    """Compatible, available donors. Contact details are never returned here."""
    groups = CAN_RECEIVE_FROM[_group(blood_group)]
    city = _clean(city)
    query = ("SELECT id, name, blood_group, city FROM donors "
             "WHERE is_available = 1 AND blood_group IN (%s)" % ",".join("?" * len(groups)))
    params = list(groups)
    if city:
        query += " AND LOWER(city) LIKE ?"
        params.append(f"%{city.lower()}%")
    with get_db() as db:
        rows = db.execute(query + " ORDER BY id DESC", params).fetchall()
    return [{"id": r["id"], "name": r["name"].split()[0],
             "blood_group": r["blood_group"], "city": r["city"]} for r in rows]


def _auth_donor(db, donor_id, token):
    row = db.execute("SELECT * FROM donors WHERE id = ?", (donor_id,)).fetchone()
    if not row:
        raise AuthError("Wrong ID or access code.")
    _check_token(row["token"], token)
    return row


def set_availability(donor_id, token, available):
    with get_db() as db:
        _auth_donor(db, donor_id, token)
        db.execute("UPDATE donors SET is_available = ? WHERE id = ?",
                   (1 if available else 0, donor_id))
    return {"is_available": bool(available)}


# ---------------- contact requests ----------------
def create_request(data):
    donor_id = _int(data.get("donor_id"), "Donor")
    seeker_group = _group(data.get("seeker_blood_group"))
    name, phone = _clean(data.get("seeker_name")), _clean(data.get("seeker_phone"))
    units = _int(data.get("units_needed"), "Units")
    urgency = _clean(data.get("urgency")).upper() or "HIGH"
    if len(name) < 2:
        raise ValidationError("Enter your name.")
    if not PHONE_RE.match(phone):
        raise ValidationError("Enter a valid phone number.")
    if not 1 <= units <= 10:
        raise ValidationError("Units must be between 1 and 10.")
    if urgency not in URGENCY_LEVELS:
        raise ValidationError("Choose a valid urgency.")
    token = secrets.token_urlsafe(8)
    with get_db() as db:
        donor = db.execute("SELECT * FROM donors WHERE id = ?", (donor_id,)).fetchone()
        if not donor or not donor["is_available"]:
            raise ValidationError("This donor is not available.")
        if donor["blood_group"] not in CAN_RECEIVE_FROM[seeker_group]:
            raise ValidationError("This donor's blood group is not compatible.")
        cur = db.execute(
            "INSERT INTO contact_requests (donor_id, seeker_name, seeker_phone, seeker_blood_group, "
            "city, units_needed, urgency, seeker_token) VALUES (?,?,?,?,?,?,?,?)",
            (donor_id, name, phone, seeker_group, donor["city"], units, urgency, token),
        )
        return {"request_id": cur.lastrowid, "access_code": token}


def donor_requests(donor_id, token):
    with get_db() as db:
        donor = _auth_donor(db, donor_id, token)
        rows = db.execute(
            "SELECT id, seeker_name, seeker_phone, seeker_blood_group, units_needed, urgency, status, created_at "
            "FROM contact_requests WHERE donor_id = ? ORDER BY id DESC", (donor_id,)).fetchall()
    return {"name": donor["name"], "blood_group": donor["blood_group"],
            "is_available": bool(donor["is_available"]), "requests": [dict(r) for r in rows]}


def respond_to_request(donor_id, token, request_id, action):
    status = {"accept": "ACCEPTED", "reject": "REJECTED"}.get(action)
    if not status:
        raise ValidationError("Action must be accept or reject.")
    with get_db() as db:
        _auth_donor(db, donor_id, token)
        cur = db.execute(
            "UPDATE contact_requests SET status = ? WHERE id = ? AND donor_id = ? AND status = 'PENDING'",
            (status, request_id, donor_id))
        if cur.rowcount == 0:
            raise ValidationError("Request not found or already answered.")
    return {"status": status}



    """Donor contact details are released only when the donor has ACCEPTED."""
    with get_db() as db:
        row = db.execute(
            "SELECT r.status, r.seeker_token, d.name, d.phone, d.email FROM contact_requests r "
            "JOIN donors d ON d.id = r.donor_id WHERE r.id = ?", (request_id,)).fetchone()
    if not row:
        raise AuthError("Wrong request ID or access code.")
    _check_token(row["seeker_token"], token)
    result = {"status": row["status"]}
    if row["status"] == "ACCEPTED":
        result["donor"] = {"name": row["name"], "phone": row["phone"], "email": row["email"]}
    return result
def request_status(request_id, token):
    """Seeker view: shows who received the request. Contact details only after ACCEPTED."""
    with get_db() as db:
        row = db.execute(
            "SELECT r.status, r.seeker_token, r.units_needed, r.urgency, r.seeker_blood_group, r.created_at, "
            "d.name, d.blood_group, d.city, d.phone, d.email FROM contact_requests r "
            "JOIN donors d ON d.id = r.donor_id WHERE r.id = ?", (request_id,)).fetchone()
    if not row:
        raise AuthError("Wrong request ID or access code.")
    _check_token(row["seeker_token"], token)
    result = {
        "status": row["status"],
        "units_needed": row["units_needed"],
        "urgency": row["urgency"],
        "seeker_blood_group": row["seeker_blood_group"],
        "sent_at": row["created_at"],
        "sent_to": {"name": row["name"].split()[0], "blood_group": row["blood_group"], "city": row["city"]},
    }
    if row["status"] == "ACCEPTED":
        result["donor"] = {"name": row["name"], "phone": row["phone"], "email": row["email"]}
    return result


def get_stats():
    """Program totals. No personal data."""
    with get_db() as db:
        donors = db.execute("SELECT COUNT(*) FROM donors").fetchone()[0]
        row = db.execute(
            "SELECT COUNT(*) AS total, "
            "COALESCE(SUM(units_needed), 0) AS sought, "
            "COALESCE(SUM(CASE WHEN status = 'ACCEPTED' THEN units_needed END), 0) AS donated, "
            "COALESCE(SUM(CASE WHEN status = 'ACCEPTED' THEN 1 END), 0) AS accepted "
            "FROM contact_requests").fetchone()
    return {"units_donated": row["donated"], "units_sought": row["sought"],
            "donors": donors, "requests": row["total"], "accepted": row["accepted"]}