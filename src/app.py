"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
import json
import time
import hashlib
import hmac
import base64

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(current_dir,
          "static")), name="static")

# Persistence path for user accounts
USERS_FILE = current_dir / "users.json"
JWT_SECRET = os.environ.get("JWT_SECRET", "replace-me-with-a-secure-secret")
JWT_ALGORITHM = "HS256"

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


def load_json_file(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return default
    return default


def save_json_file(path, data):
    path.write_text(json.dumps(data, indent=2))


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, hashed_password: str) -> bool:
    return hash_password(password) == hashed_password


def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def base64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def sign_token(message: bytes) -> str:
    signature = hmac.new(JWT_SECRET.encode("utf-8"), message, hashlib.sha256).digest()
    return base64url_encode(signature)


def create_jwt(payload: dict, expires_in: int = 3600) -> str:
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    payload_data = payload.copy()
    payload_data["exp"] = int(time.time()) + expires_in

    header_b64 = base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = base64url_encode(json.dumps(payload_data, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = sign_token(signing_input)

    return f"{header_b64}.{payload_b64}.{signature}"


def decode_jwt(token: str) -> dict:
    try:
        header_b64, payload_b64, signature = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_signature = sign_token(signing_input)

        if not hmac.compare_digest(expected_signature, signature):
            raise ValueError("Invalid token signature")

        payload = json.loads(base64url_decode(payload_b64).decode("utf-8"))
        if payload.get("exp", 0) < int(time.time()):
            raise ValueError("Token has expired")

        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def ensure_users_file():
    users = load_json_file(USERS_FILE, [])
    if not users:
        save_json_file(USERS_FILE, [
            {
                "email": "teacher@mergington.edu",
                "password": hash_password("adminpass"),
                "role": "admin",
                "name": "Teacher",
                "created_at": int(time.time())
            }
        ])


def get_user_by_email(email: str):
    users = load_json_file(USERS_FILE, [])
    normalized_email = email.strip().lower()
    for user in users:
        if user.get("email") == normalized_email:
            return user
    return None


def save_user(user: dict):
    users = load_json_file(USERS_FILE, [])
    users.append(user)
    save_json_file(USERS_FILE, users)


def public_user(user: dict) -> dict:
    return {k: v for k, v in user.items() if k != "password"}


def get_current_user(authorization: str = Header(default=None, alias="Authorization")):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.split(" ", 1)[1]
    payload = decode_jwt(token)
    user = get_user_by_email(payload.get("email", ""))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/users/register")
def register_user(user: dict):
    ensure_users_file()
    email = user.get("email", "").strip().lower()
    password = user.get("password", "")
    name = user.get("name", "")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    if get_user_by_email(email):
        raise HTTPException(status_code=400, detail="Email already in use")

    new_user = {
        "email": email,
        "password": hash_password(password),
        "role": "student",
        "name": name,
        "created_at": int(time.time())
    }
    save_user(new_user)

    token = create_jwt({"email": email, "role": new_user["role"]})
    return {"token": token, "user": public_user(new_user)}


@app.post("/users/login")
def login_user(credentials: dict):
    email = credentials.get("email", "").strip().lower()
    password = credentials.get("password", "")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    user = get_user_by_email(email)
    if not user or not verify_password(password, user.get("password", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_jwt({"email": email, "role": user.get("role", "student")})
    return {"token": token, "user": public_user(user)}


@app.get("/users/me")
def get_me(authorization: str = Header(default=None, alias="Authorization")):
    user = get_current_user(authorization)
    return public_user(user)


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str = None,
                       authorization: str = Header(default=None, alias="Authorization")):
    """Sign up a student for an activity"""
    current_user = get_current_user(authorization)
    if current_user["role"] == "student":
        email = current_user["email"]
    else:
        email = (email or current_user["email"]).strip().lower()

    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = activities[activity_name]
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str = None,
                             authorization: str = Header(default=None, alias="Authorization")):
    """Unregister a student from an activity"""
    current_user = get_current_user(authorization)
    if current_user["role"] == "student":
        email = current_user["email"]
    else:
        email = (email or current_user["email"]).strip().lower()

    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = activities[activity_name]
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
