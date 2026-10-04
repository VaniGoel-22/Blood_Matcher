# Dynamic Emergency Blood Matcher

Track 02 | Healthcare & Life Safety. A Flask + SQLite app that matches emergency blood seekers with compatible, available donors while keeping donor contact details private.

## Structure

```
Blood_Matcher/
├── backend/
│   ├── app.py        # Flask routes, serves the frontend
│   ├── database.py   # SQLite connection and tables
│   └── models.py     # compatibility rules, validation, privacy logic
├── frontend/
│   ├── index.html
│   └── styles.css
├── requirements.txt
└── README.md
```

## Run

```powershell
pip install -r requirements.txt
python backend\app.py
```
Open http://127.0.0.1:5000

## How it works

1. A donor registers (blood group, city, phone, email). They receive a donor ID and an access code.
2. A seeker searches by blood group and city. Results show only first name, blood group and city.
3. The seeker sends a contact request and receives a request ID and access code.
4. The donor opens "Donor dashboard" with their ID and access code, then accepts or rejects.
5. Only after acceptance can the seeker see the donor's phone and email.

## Blood compatibility

| Recipient | Can receive from |
|-----------|------------------|
| A+  | A+, A-, O+, O- |
| A-  | A-, O- |
| B+  | B+, B-, O+, O- |
| B-  | B-, O- |
| AB+ | all groups |
| AB- | AB-, A-, B-, O- |
| O+  | O+, O- |
| O-  | O- |

## API

| Method | Route | Purpose |
|--------|-------|---------|
| POST | `/api/donors` | Register a donor |
| GET | `/api/search?blood_group=&city=` | Search compatible donors (no contact info) |
| POST | `/api/requests` | Send a contact request |
| GET | `/api/requests/<id>?code=` | Seeker checks status; contact shown only if accepted |
| GET | `/api/donors/<id>/requests?code=` | Donor lists requests |
| POST | `/api/donors/<id>/requests/<rid>` | Donor accepts or rejects |
| POST | `/api/donors/<id>/availability` | Donor toggles availability |
