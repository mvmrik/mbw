# SPS Calculator - encode and decode seed phrases
# Algorithm: result[i] = word_index * char_value(pass1[i]) * char_value(pass2[i])
# char_value: a=1..z=26, A=1..Z=26, 0=1..9=9 (digits: '0'->1, '1'->2, ..., '9'->10... wait)
# Per user spec: digits are their numeric value, letters are their alphabetical position
# digits: '0'=0? No - user said "номера на буквите е от поредността им - A е 1"
# For digits: '1'=1, '2'=2, ..., '9'=9, '0'=10 (or treat as positional: 0->10 to avoid zero multiply)
# We use: letters a-z/A-Z -> 1-26, digits 1-9 -> 1-9, digit 0 -> 10 (to avoid zero)

from bip39_wordlist import get_word_index, get_word_by_index


def char_value(ch: str) -> int:
    """
    Returns numeric value of a character:
    - a/A=1, b/B=2, ..., z/Z=26
    - '1'=1, '2'=2, ..., '9'=9, '0'=10
    """
    ch = ch.lower()
    if ch.isalpha():
        return ord(ch) - ord('a') + 1
    elif ch.isdigit():
        if ch == '0':
            return 10
        return int(ch)
    return 0


def validate_password(password: str, length: int, n: int):
    """
    Validates password. Returns error string or None if valid.
    n = 1 or 2 (which password)
    """
    if len(password) != length:
        return f"password_length:{n}:{length}"
    for ch in password:
        if not (ch.isalpha() and ch.isascii()) and not ch.isdigit():
            return f"password_chars:{n}"
    return None


def encode(words: list, pass1: str, pass2: str):
    """
    Encodes seed phrase words using two passwords.
    Returns (list of encoded numbers, None) on success,
    or (None, error_key_with_params) on failure.
    """
    n = len(words)

    # Validate word count
    if n not in (12, 18, 24):
        return None, "err_word_count"

    # Validate passwords
    for i, pwd in enumerate([pass1, pass2], 1):
        err = validate_password(pwd, n, i)
        if err:
            parts = err.split(":")
            if parts[1] == "length":
                return None, f"err_password_length:n={i}:length={n}"
            else:
                return None, f"err_password_chars:n={i}"

    # Encode each word
    result = []
    for i, word in enumerate(words):
        idx = get_word_index(word)
        if idx == 0:
            return None, f"err_invalid_word:word={word}:pos={i+1}"
        v1 = char_value(pass1[i])
        v2 = char_value(pass2[i])
        result.append(idx * v1 * v2)

    return result, None


def decode(encoded: list, pass1: str, pass2: str):
    """
    Decodes encoded numbers back to seed phrase words.
    Returns (list of words, None) on success,
    or (None, error) on failure.
    """
    n = len(encoded)

    if n not in (12, 18, 24):
        return None, "err_word_count"

    # Validate passwords
    for i, pwd in enumerate([pass1, pass2], 1):
        err = validate_password(pwd, n, i)
        if err:
            parts = err.split(":")
            if "length" in parts[1]:
                return None, f"err_password_length:n={i}:length={n}"
            else:
                return None, f"err_password_chars:n={i}"

    words = []
    for i, val in enumerate(encoded):
        v1 = char_value(pass1[i])
        v2 = char_value(pass2[i])
        divisor = v1 * v2
        if divisor == 0:
            return None, f"err_decode_failed:pos={i+1}:val={val}"
        if val % divisor != 0:
            return None, f"err_decode_failed:pos={i+1}:val={val}"
        word_idx = val // divisor
        word = get_word_by_index(word_idx)
        if not word:
            return None, f"err_decode_failed:pos={i+1}:val={word_idx}"
        words.append(word)

    return words, None


def parse_encoded_string(encoded_str: str, expected_n=None):
    """
    Parses a dash-separated encoded string into list of integers.
    Returns (list, None) on success or (None, error) on failure.
    """
    parts = encoded_str.strip().split("-")
    n = len(parts)

    if expected_n is not None and n != expected_n:
        return None, f"err_encoded_format:n={expected_n}"

    if n not in (12, 18, 24):
        return None, f"err_encoded_format:n={n}"

    numbers = []
    for i, p in enumerate(parts):
        try:
            numbers.append(int(p.strip()))
        except ValueError:
            return None, f"err_encoded_number:pos={i+1}"

    return numbers, None


def format_encoded(numbers: list[int]) -> str:
    """Formats list of numbers as dash-separated string."""
    return "-".join(str(n) for n in numbers)
