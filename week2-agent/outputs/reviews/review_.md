# Code Review: test_targets/

## Summary

The `test_targets/` directory contains three Python files representing common coding mistakes across security, correctness, and performance dimensions. The code is small but dense with bugs: SQL injection, path traversal, timing attacks, mutable default arguments, bare except clauses, hardcoded credentials, and O(n²) algorithms. No issues were flagged by pyflakes, demonstrating that static analysis tools cannot catch semantic and security bugs. All complexity scores were low (A range), confirming that complexity metrics also miss these classes of bugs.

---

## File: `buggy_api.py`

### [HIGH] SQL Injection in `get_user()`
**Location:** `get_user()`, line 29
**Description:** User input is interpolated directly into a SQL query using an f-string. An attacker can inject arbitrary SQL to bypass authentication or exfiltrate data.
**Reproduction:**
```python
username = "admin' OR '1'='1"
query = f"SELECT * FROM users WHERE username = '{username}'"
# Produces: SELECT * FROM users WHERE username = 'admin' OR '1'='1'
# This returns all users, bypassing authentication
```
**Fix:** Use parameterized queries: `db_cursor.execute("SELECT * FROM users WHERE username = %s", (username,))`

---

### [HIGH] Path Traversal in `read_user_file()` (insecure_auth.py)
**Location:** `read_user_file()`, line 8
**Description:** The `username` parameter is used to construct a file path without sanitization. An attacker can use `../` sequences to read arbitrary files on the system.
**Reproduction:**
```python
username = "../../etc/passwd"
path = f"/app/user_data/{username}/profile.txt"
# Produces: /app/user_data/../../etc/passwd/profile.txt
# Resolves to: /etc/passwd/profile.txt (or /etc/passwd with more ../)
```
**Fix:** Validate that the resolved path stays within the expected directory using `os.path.realpath()` and prefix checking.

---

### [HIGH] Timing Attack Vulnerability in `verify_token()`
**Location:** `verify_token()`, line 5
**Description:** Uses `==` for comparing security tokens, which short-circuits on the first mismatched byte. An attacker can measure response times to deduce the correct token byte-by-byte.
**Reproduction:**
```python
# == comparison short-circuits on first mismatch
"secret_password_123" == "xecret_password_123"  # Fast return False
# hmac.compare_digest takes constant time regardless of where mismatch occurs
```
**Fix:** Use `hmac.compare_digest(provided, expected)` for constant-time comparison.

---

### [CRITICAL] Hardcoded Credentials
**Location:** `insecure_auth.py`, lines 1-2, 12-15
**Description:** `SECRET_KEY`, `DB_PASSWORD`, and plaintext user passwords are hardcoded in source code. If the code is leaked (e.g., via version control), all credentials are immediately compromised.
**Reproduction:**
```python
SECRET_KEY = "super_secret_123"
DB_PASSWORD = "admin1234"
users_db = {"alice": "password123", "bob": "qwerty"}
# All secrets visible in plain text
```
**Fix:** Load secrets from environment variables or a secrets manager (e.g., AWS Secrets Manager, HashiCorp Vault).

---

### [MEDIUM] Mutable Default Argument in `add_item()`
**Location:** `add_item()`, line 3
**Description:** `cart=[]` creates a single list object shared across all calls. Items added in previous calls persist, causing unexpected behavior.
**Reproduction:**
```python
def add_item(item, cart=[]):
    cart.append(item)
    return cart

add_item("apple")   # Returns ['apple']
add_item("banana")  # Returns ['apple', 'banana'] — unexpected!
```
**Fix:** Use `cart=None` and initialize inside the function: `if cart is None: cart = []`

---

### [MEDIUM] Bare `except` Clause in `load_config()`
**Location:** `load_config()`, line 9
**Description:** A bare `except:` catches all exceptions including `KeyboardInterrupt`, `SystemExit`, and `MemoryError`. This silently swallows errors, making debugging impossible and potentially masking critical failures.
**Reproduction:**
```python
try:
    with open(path) as f:
        return json.load(f)
except:
    return {}  # Catches KeyboardInterrupt, SystemExit, SyntaxError, etc.
```
**Fix:** Catch specific exceptions: `except (FileNotFoundError, json.JSONDecodeError):`

---

### [MEDIUM] `find_duplicates()` Returns Non-Unique Duplicates
**Location:** `find_duplicates()`, line 20
**Description:** If an item appears more than twice, it is added to `duplicates` multiple times. The function name implies unique duplicates but the implementation does not guarantee this.
**Reproduction:**
```python
def find_duplicates(items):
    seen = []
    duplicates = []
    for item in items:
        if item in seen:
            duplicates.append(item)
        seen.append(item)
    return duplicates

find_duplicates([1, 2, 3, 2, 1, 1, 1, 2])
# Returns: [2, 1, 1, 1, 2] instead of [1, 2]
```
**Fix:** Use a set to track already-reported duplicates, or use `collections.Counter`.

---

### [LOW] O(n²) Performance in `find_duplicates()`
**Location:** `find_duplicates()`, line 20
**Description:** Using a list for `seen` makes the `item in seen` check O(n), resulting in O(n²) overall complexity. A set would make this O(n).
**Reproduction:**
```python
# With list: O(n) lookup × n items = O(n²)
# With set:  O(1) lookup × n items = O(n)
# For large inputs, this difference is significant
```
**Fix:** Use a `set` for `seen` (and another set for `duplicates` if uniqueness is desired).

---

## File: `inefficient_sort.py`

### [LOW] Empty File
**Location:** entire file
**Description:** The file is 0 bytes. This appears to be a placeholder or an incomplete submission. No code to review.

---

## Summary of Issues by Severity

| Severity | Count | Issues |
|----------|-------|--------|
| CRITICAL | 1 | Hardcoded credentials |
| HIGH | 3 | SQL injection, Path traversal, Timing attack |
| MEDIUM | 3 | Mutable default arg, Bare except, Non-unique duplicates |
| LOW | 2 | O(n²) performance, Empty file |

**Total: 9 issues found across 3 files**
