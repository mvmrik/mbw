# SPS Calculator - encode and decode seed phrases
#
# Algorithm:
#   char_value: a-z = 1-26, A-Z = 27-52  (no digits)
#   encode[i] = word_index * char_value(pass1[i]) * char_value(pass2[i])
#   shuffle: sort encoded numbers by (char_value(pass1[i]) + char_value(pass2[i])),
#            stable sort (equal sums keep original order)
#
# Decode is the reverse: unshuffle using the same sums, then divide to get word_index.

from bip39_wordlist import get_word_index, get_word_by_index


def char_value(ch: str) -> int:
    """
    Returns numeric value of a character:
    - a-z = 1-26
    - A-Z = 27-52
    """
    if ch.islower():
        return ord(ch) - ord('a') + 1
    elif ch.isupper():
        return ord(ch) - ord('A') + 27
    return 0


def validate_password(password: str, length: int, n: int):
    """
    Validates password. Returns error string or None if valid.
    n = 1 or 2 (which password)
    """
    if len(password) != length:
        return f"password_length:{n}:{length}"
    for ch in password:
        if not (ch.isalpha() and ch.isascii()):
            return f"password_chars:{n}"
    return None


def _shuffle_order(pass1: str, pass2: str) -> list:
    """
    Returns the shuffle order: a list of original indices sorted by
    (char_value(pass1[i]) + char_value(pass2[i])), stable sort.
    """
    n = len(pass1)
    sums = [(char_value(pass1[i]) + char_value(pass2[i]), i) for i in range(n)]
    sums.sort(key=lambda x: x[0])  # stable sort — Python's sort is stable
    return [x[1] for x in sums]


def encode(words: list, pass1: str, pass2: str):
    """
    Encodes seed phrase words using two passwords.
    Returns (list of shuffled encoded numbers, None) on success,
    or (None, error_key_with_params) on failure.
    """
    n = len(words)

    if n not in (12, 18, 24):
        return None, "err_word_count"

    for i, pwd in enumerate([pass1, pass2], 1):
        err = validate_password(pwd, n, i)
        if err:
            parts = err.split(":")
            if parts[1] == "length":
                return None, f"err_password_length:n={i}:length={n}"
            else:
                return None, f"err_password_chars:n={i}"

    # Step 1: encode each word at its original position
    encoded = []
    for i, word in enumerate(words):
        idx = get_word_index(word)
        if idx == 0:
            return None, f"err_invalid_word:word={word}:pos={i+1}"
        v1 = char_value(pass1[i])
        v2 = char_value(pass2[i])
        encoded.append(idx * v1 * v2)

    # Step 2: shuffle — reorder encoded numbers by sum of char values
    order = _shuffle_order(pass1, pass2)
    shuffled = [encoded[i] for i in order]

    return shuffled, None


def decode(encoded: list, pass1: str, pass2: str):
    """
    Decodes shuffled encoded numbers back to seed phrase words.
    Returns (list of words in original order, None) on success,
    or (None, error) on failure.
    """
    n = len(encoded)

    if n not in (12, 18, 24):
        return None, "err_word_count"

    for i, pwd in enumerate([pass1, pass2], 1):
        err = validate_password(pwd, n, i)
        if err:
            parts = err.split(":")
            if "length" in parts[1]:
                return None, f"err_password_length:n={i}:length={n}"
            else:
                return None, f"err_password_chars:n={i}"

    # Step 1: unshuffle — find original positions
    order = _shuffle_order(pass1, pass2)
    # order[j] = original index that ended up at shuffled position j
    # We need the reverse: unshuffled[original_i] = shuffled[j]
    unshuffled = [None] * n
    for j, orig_i in enumerate(order):
        unshuffled[orig_i] = encoded[j]

    # Step 2: decode each number at its original position
    words = []
    for i, val in enumerate(unshuffled):
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


def format_encoded(numbers: list) -> str:
    """Formats list of numbers as dash-separated string."""
    return "-".join(str(n) for n in numbers)
