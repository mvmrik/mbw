# Internationalization - translations for the app
# To add a new language, add a new key in TRANSLATIONS dict

TRANSLATIONS = {
    "en": {
        # App
        "app_title": "My Bitcoin World",
        "tab_sps": "SPS",
        "tab_settings": "Settings",

        # SPS Tab
        "sps_title": "Seed Phrase Storage Calculator",
        "sps_description": (
            "Enter your seed phrase words, then two sentences (passwords) equal in length to the number of words.\n"
            "Only Latin letters (a-z, A-Z) are allowed. No digits or special characters."
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
        "chars_remaining": "{n} remaining",
        "chars_ok": "✓ Length OK",
        "word_valid": "✓",
        "word_invalid": "✗ unknown word",
        "word_duplicate": "✗ duplicate",

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
        "err_duplicate_words": "Duplicate words detected. Each word must be unique.",

        # Settings Tab
        "settings_title": "Settings",
        "label_language": "Language:",
        "btn_save_settings": "Save Settings",
        "settings_saved": "Settings saved.",

        # Portfolio Tab
        "tab_portfolio": "Portfolio",
        "portfolio_title": "Bitcoin Portfolio",
        "portfolio_total": "Total Balance:",
        "portfolio_btc_price": "BTC Price:",
        "portfolio_last_updated": "Last updated:",
        "portfolio_never": "never",
        "portfolio_offline": "offline",
        "btn_refresh": "⟳ Refresh",
        "btn_add_address": "+ Add Address",
        "label_address": "BTC Address:",
        "label_addr_label": "Label (optional):",
        "placeholder_address": "bc1q... or 1... or 3...",
        "placeholder_label": "e.g. Cold wallet",
        "btn_save_address": "Add",
        "btn_cancel": "Cancel",
        "btn_remove_address": "Remove",
        "confirm_remove": "Remove address '{label}'?",
        "portfolio_no_addresses": "No addresses yet. Click '+ Add Address' to get started.",
        "portfolio_balance_unknown": "balance unknown",
        "portfolio_refreshing": "Refreshing...",
        "portfolio_refresh_done": "Updated successfully.",
        "portfolio_refresh_errors": "Updated with errors:\n{errors}",
        "err_empty_address": "Please enter a BTC address.",
        "err_invalid_address": "Invalid BTC address format.",
        "err_duplicate_address": "This address is already in your portfolio.",

        "tab_help": "Help",
        "label_algorithm": "How the calculation works:",
        "text_algorithm": (
            "LETTER VALUES:  a-z = 1 to 26  |  A-Z = 27 to 52\n"
            "\n"
            "ENCODE (words → numbers)\n"
            "  Step 1 — Code each word:\n"
            "    number[i]  =  word_index[i]  ×  value(sentence1[i])  ×  value(sentence2[i])\n"
            "    word_index = position of the word in the BIP39 list (abandon=1 ... zoo=2048)\n"
            "\n"
            "  Step 2 — Shuffle:\n"
            "    sum[i]  =  value(sentence1[i])  +  value(sentence2[i])\n"
            "    Sort the 24 numbers by their sum (smallest sum first).\n"
            "    Equal sums keep their original order (stable sort).\n"
            "\n"
            "DECODE (numbers → words)\n"
            "  Step 1 — Find the original order:\n"
            "    Calculate the same 24 sums from both sentences.\n"
            "    Sort positions by sum — this tells you which number belongs where.\n"
            "\n"
            "  Step 2 — Recover each word:\n"
            "    word_index[i]  =  number  ÷  (value(sentence1[i])  ×  value(sentence2[i]))\n"
            "    Look up the word at that index in the BIP39 list."
        ),

        "label_bip39_list": "BIP39 Word List (2048 words):",
        "desc_bip39_list": "These are all valid seed phrase words in order. The number on the left is the index used in the calculation.",
        "btn_show_bip39": "Show BIP39 word list...",
        "bip39_loading": "Loading 2048 words...",

        # Backup
        "label_backup": "Backup & Restore",
        "desc_backup": "Export all your settings and portfolio addresses to a JSON file. Import on another device to restore everything.",
        "btn_export": "Export backup...",
        "btn_import": "Import backup...",
        "export_ok": "Backup exported successfully.",
        "import_ok": "Backup imported. Reloading...",
        "import_err_format": "Invalid backup file format.",
        "import_confirm": "This will overwrite your current settings and portfolio. Continue?",

        # Languages
        "lang_en": "English",
        "lang_bg": "Bulgarian",
    },

    "bg": {
        # App
        "app_title": "My Bitcoin World",
        "tab_sps": "SPS",
        "tab_settings": "Настройки",

        # SPS Tab
        "sps_title": "Калкулатор за Seed Phrase",
        "sps_description": (
            "Въведете думите от вашата seed фраза, след това две изречения с дължина равна на броя думи.\n"
            "Разрешени са само латински букви (a-z, A-Z). Без цифри или специални символи."
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
        "chars_remaining": "остават {n}",
        "chars_ok": "✓ Дължината е ОК",
        "word_valid": "✓",
        "word_invalid": "✗ непозната дума",
        "word_duplicate": "✗ дублирана",

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
        "err_duplicate_words": "Открити са дублирани думи. Всяка дума трябва да е уникална.",

        # Settings Tab
        "settings_title": "Настройки",
        "label_language": "Език:",
        "btn_save_settings": "Запази Настройките",
        "settings_saved": "Настройките са запазени.",

        # Portfolio Tab
        "tab_portfolio": "Портфолио",
        "portfolio_title": "Bitcoin Портфолио",
        "portfolio_total": "Общо Салдо:",
        "portfolio_btc_price": "Цена на BTC:",
        "portfolio_last_updated": "Последно обновено:",
        "portfolio_never": "никога",
        "portfolio_offline": "офлайн",
        "btn_refresh": "⟳ Обнови",
        "btn_add_address": "+ Добави Адрес",
        "label_address": "BTC Адрес:",
        "label_addr_label": "Етикет (по желание):",
        "placeholder_address": "bc1q... или 1... или 3...",
        "placeholder_label": "напр. Студен портфейл",
        "btn_save_address": "Добави",
        "btn_cancel": "Отказ",
        "btn_remove_address": "Премахни",
        "confirm_remove": "Премахване на адрес '{label}'?",
        "portfolio_no_addresses": "Няма адреси. Натиснете '+ Добави Адрес' за начало.",
        "portfolio_balance_unknown": "балансът е неизвестен",
        "portfolio_refreshing": "Обновяване...",
        "portfolio_refresh_done": "Обновено успешно.",
        "portfolio_refresh_errors": "Обновено с грешки:\n{errors}",
        "err_empty_address": "Моля въведете BTC адрес.",
        "err_invalid_address": "Невалиден формат на BTC адрес.",
        "err_duplicate_address": "Този адрес вече е в портфолиото.",

        "tab_help": "Помощ",
        "label_algorithm": "Как се пресмята:",
        "text_algorithm": (
            "СТОЙНОСТИ НА БУКВИТЕ:  a-z = 1 до 26  |  A-Z = 27 до 52\n"
            "\n"
            "КОДИРАНЕ (думи → числа)\n"
            "  Стъпка 1 — Кодирай всяка дума:\n"
            "    число[i]  =  индекс_на_дума[i]  ×  стойност(изречение1[i])  ×  стойност(изречение2[i])\n"
            "    индекс = позицията на думата в BIP39 списъка (abandon=1 ... zoo=2048)\n"
            "\n"
            "  Стъпка 2 — Разбъркване:\n"
            "    сума[i]  =  стойност(изречение1[i])  +  стойност(изречение2[i])\n"
            "    Подреди 24-те числа по нарастваща сума.\n"
            "    При равни суми — запази оригиналния ред (stable sort).\n"
            "\n"
            "ДЕКОДИРАНЕ (числа → думи)\n"
            "  Стъпка 1 — Намери оригиналния ред:\n"
            "    Изчисли същите 24 суми от двете изречения.\n"
            "    Подреди позициите по сума — така знаеш кое число на коя позиция е.\n"
            "\n"
            "  Стъпка 2 — Възстанови думите:\n"
            "    индекс[i]  =  число  ÷  (стойност(изречение1[i])  ×  стойност(изречение2[i]))\n"
            "    Намери думата с този индекс в BIP39 списъка."
        ),

        "label_bip39_list": "BIP39 Списък с думи (2048 думи):",
        "desc_bip39_list": "Всички валидни думи за seed фраза по ред. Числото вляво е индексът, използван при пресмятането.",
        "btn_show_bip39": "Покажи BIP39 списък с думи...",
        "bip39_loading": "Зарежда 2048 думи...",

        # Backup
        "label_backup": "Архивиране и възстановяване",
        "desc_backup": "Експортирай всички настройки и адреси от портфолиото в JSON файл. Импортирай на друго устройство за да възстановиш всичко.",
        "btn_export": "Експортирай архив...",
        "btn_import": "Импортирай архив...",
        "export_ok": "Архивът е експортиран успешно.",
        "import_ok": "Архивът е импортиран. Презарежда...",
        "import_err_format": "Невалиден формат на архивния файл.",
        "import_confirm": "Това ще презапише текущите ти настройки и портфолио. Продължи?",

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
