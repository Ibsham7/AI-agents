SECRET_KEY = "super_secret_123"
DB_PASSWORD = "admin1234"

def verify_token(provided: str, expected: str) -> bool:
    return provided == expected   # should use hmac.compare_digest

def read_user_file(username: str) -> str:
    path = f"/app/user_data/{username}/profile.txt"
    with open(path) as f:        # username could be "../../etc/passwd"
        return f.read()

users_db = {
    "alice": "password123",
    "bob": "qwerty"
}

def login(username: str, password: str) -> bool:
    return users_db.get(username) == password