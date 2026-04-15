# Internationalization - translations for the app
# To add a new language, add a new key in TRANSLATIONS dict

TRANSLATIONS = {
    "en": {
        # App
        "app_title": "SPS - Seed Phrase Storage",
        "tab_sps": "SPS",
        "tab_settings": "Settings",

        # SPS Tab
        "sps_title": "Seed Phrase Storage Calculator",
        "sps_description": (
            "Enter your seed phrase words, then two passwords equal in length to the number of words.\n"
            "Only Latin letters (a-z, A-Z) and digits (0-9) are allowed in passwords. No special characters."
        ),
        "label_seed_words": "Seed Phrase Words (12, 18 or 24):",
        "placeholder_word": "word",
        "label_password1": "Password 1:",
        "label_password2": "Password 2:",
        "placeholder_password": "Letters and digits only, length = number of words",
        "btn_encode": "Encode → Generate Code",
        "btn_decode": "Decode → Recover Words",
        "btn_clear": "Clear All",
        "label_result": "Result:",
        "copy_result": "Copy to Clipboard",
        "copied": "Copied!",

        # Decode input
        "label_encoded_input": "Encoded Code (paste here):",
        "placeholder_encoded": "1234-5678-...",

        # Errors
        "err_word_count": "Number of words must be 12, 18 or 24.",
        "err_invalid_word": "Unknown BIP-39 word: '{word}' (position {pos})",
        "err_password_length": "Password {n} must be exactly {length} characters (same as word count).",
        "err_password_chars": "Password {n} contains invalid characters. Only letters a-z and digits 0-9 allowed.",
        "err_encoded_format": "Invalid encoded format. Expected {n} numbers separated by dashes.",
        "err_encoded_number": "Segment {pos} is not a valid number.",
        "err_decode_failed": "Could not decode segment {pos}: result {val} is not a valid BIP-39 index.",
        "err_empty_words": "Please enter your seed phrase words.",
        "err_empty_passwords": "Please enter both passwords.",
        "err_empty_encoded": "Please enter the encoded code.",

        # Settings Tab
        "settings_title": "Settings",
        "label_language": "Language:",
        "btn_save_settings": "Save Settings",
        "settings_saved": "Settings saved.",

        # Languages
        "lang_en": "English",
        "lang_bg": "Bulgarian",
    },

    "bg": {
        # App
        "app_title": "SPS - Съхранение на Seed Phrase",
        "tab_sps": "SPS",
        "tab_settings": "Настройки",

        # SPS Tab
        "sps_title": "Калкулатор за Seed Phrase",
        "sps_description": (
            "Въведете думите от вашата seed фраза, след това две пароли с дължина равна на броя думи.\n"
            "Паролите трябва да съдържат само латински букви (a-z, A-Z) и цифри (0-9). Без специални символи."
        ),
        "label_seed_words": "Думи от Seed Phrase (12, 18 или 24):",
        "placeholder_word": "дума",
        "label_password1": "Парола 1:",
        "label_password2": "Парола 2:",
        "placeholder_password": "Само букви и цифри, дължина = брой думи",
        "btn_encode": "Кодирай → Генерирай Код",
        "btn_decode": "Декодирай → Възстанови Думите",
        "btn_clear": "Изчисти Всичко",
        "label_result": "Резултат:",
        "copy_result": "Копирай в Клипборда",
        "copied": "Копирано!",

        # Decode input
        "label_encoded_input": "Кодиран Код (постави тук):",
        "placeholder_encoded": "1234-5678-...",

        # Errors
        "err_word_count": "Броят думи трябва да е 12, 18 или 24.",
        "err_invalid_word": "Непозната BIP-39 дума: '{word}' (позиция {pos})",
        "err_password_length": "Парола {n} трябва да е точно {length} символа (равно на броя думи).",
        "err_password_chars": "Парола {n} съдържа невалидни символи. Разрешени са само букви a-z и цифри 0-9.",
        "err_encoded_format": "Невалиден формат. Очакват се {n} числа разделени с тирета.",
        "err_encoded_number": "Сегмент {pos} не е валидно число.",
        "err_decode_failed": "Не може да се декодира сегмент {pos}: резултат {val} не е валиден BIP-39 индекс.",
        "err_empty_words": "Моля въведете думите от вашата seed фраза.",
        "err_empty_passwords": "Моля въведете двете пароли.",
        "err_empty_encoded": "Моля въведете кодирания код.",

        # Settings Tab
        "settings_title": "Настройки",
        "label_language": "Език:",
        "btn_save_settings": "Запази Настройките",
        "settings_saved": "Настройките са запазени.",

        # Languages
        "lang_en": "English",
        "lang_bg": "Български",
    }
}

AVAILABLE_LANGUAGES = {
    "en": "English",
    "bg": "Български",
}

def t(lang: str, key: str, **kwargs) -> str:
    """Get translated string for given language and key."""
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    text = lang_dict.get(key, TRANSLATIONS["en"].get(key, key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return text
