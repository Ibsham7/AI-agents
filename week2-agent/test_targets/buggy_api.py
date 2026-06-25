import json

def add_item(item, cart=[]):
    cart.append(item)
    return cart

def load_config(path):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return {}

def get_pairs(items):
    pairs = []
    for i in range(len(items) - 1):
        pairs.append((items[i], items[i+1]))
    return pairs

def find_duplicates(items):
    seen = []
    duplicates = []
    for item in items:
        if item in seen:        
            duplicates.append(item)
        seen.append(item)
    return duplicates

def get_user(db_cursor, username):
    query = f"SELECT * FROM users WHERE username = '{username}'"
    db_cursor.execute(query)
    return db_cursor.fetchone()