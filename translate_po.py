from pathlib import Path

import polib
from deep_translator import GoogleTranslator


PO_FILE = str(input("Введите путь к .po файлу (locale/ru/LC_MESSAGES/django.po): "))

SOURCE_LANG = "en"
TARGET_LANG = str(input("Введите язык перевода (например, 'ru'): "))


def translate_po_file():
    po_path = Path(PO_FILE)

    if not po_path.exists():
        print(f"❌ Файл не найден: {po_path}")
        return

    po = polib.pofile(str(po_path))

    translator = GoogleTranslator(
        source=SOURCE_LANG,
        target=TARGET_LANG,
    )

    translated = 0
    skipped = 0
    errors = 0

    for entry in po:

        # Пустой msgid
        if not entry.msgid.strip():
            skipped += 1
            continue

        # Уже переведено
        if entry.msgstr.strip():
            skipped += 1
            continue

        # fuzzy
        if "fuzzy" in entry.flags:
            skipped += 1
            continue

        try:
            translated_text = translator.translate(entry.msgid)

            entry.msgstr = translated_text

            translated += 1

            print(
                f"✅ {entry.msgid}"
                f" → {entry.msgstr}"
            )

        except Exception as e:
            errors += 1

            print(
                f"❌ Ошибка: {entry.msgid}"
            )
            print(f"   {e}")

    po.save(str(po_path))

    print("\n==========================")
    print("Перевод завершён")
    print("==========================")
    print(f"Переведено: {translated}")
    print(f"Пропущено:  {skipped}")
    print(f"Ошибок:     {errors}")
    print(f"Файл:       {po_path}")


if __name__ == "__main__":
    translate_po_file()