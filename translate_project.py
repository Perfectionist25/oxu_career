#!/usr/bin/env python3
"""
Улучшенный скрипт для автоматического перевода Django проекта
с английского на узбекский и русский
"""

import os
import sys
import polib
import time
import requests
import json
from pathlib import Path
from deep_translator import GoogleTranslator, LingueeTranslator
import django

# Добавляем путь к проекту Django в PYTHONPATH
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Настройки Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

class AdvancedProjectTranslator:
    def __init__(self):
        self.target_languages = ['uz', 'ru']
        self.source_language = 'en'
        self.translated_count = 0
        self.skipped_count = 0
        self.error_count = 0
        
        # Глоссарий для консистентного перевода технических терминов
        self.glossary = {
            'en': {
                'uz': {
                    'login': 'tizimga kirish',
                    'password': 'parol',
                    'email': 'elektron pochta',
                    'submit': 'yuborish',
                    'save': 'saqlash',
                    'cancel': 'bekor qilish',
                    'delete': 'oʻchirish',
                    'edit': 'tahrirlash',
                    'create': 'yaratish',
                    'update': 'yangilash',
                    'search': 'qidirish',
                    'filter': 'filtrlash',
                    'settings': 'sozlamalar',
                    'profile': 'profil',
                    'dashboard': 'boshqaruv paneli',
                    'admin': 'administrator',
                    'user': 'foydalanuvchi',
                    'job': 'ish',
                    'company': 'kompaniya',
                    'application': 'ariza',
                    'resume': 'rezyume',
                    'salary': 'maosh',
                    'experience': 'tajriba',
                    'skills': 'koʻnikmalar',
                    'remote': 'masofaviy',
                    'hybrid': 'gibrid',
                    'office': 'ofis',
                    'full-time': 'toʻliq stavka',
                    'part-time': 'qisman stavka',
                },
                'ru': {
                    'login': 'вход в систему',
                    'password': 'пароль',
                    'email': 'электронная почта',
                    'submit': 'отправить',
                    'save': 'сохранить',
                    'cancel': 'отмена',
                    'delete': 'удалить',
                    'edit': 'редактировать',
                    'create': 'создать',
                    'update': 'обновить',
                    'search': 'поиск',
                    'filter': 'фильтр',
                    'settings': 'настройки',
                    'profile': 'профиль',
                    'dashboard': 'панель управления',
                    'admin': 'администратор',
                    'user': 'пользователь',
                    'job': 'работа',
                    'company': 'компания',
                    'application': 'заявка',
                    'resume': 'резюме',
                    'salary': 'зарплата',
                    'experience': 'опыт',
                    'skills': 'навыки',
                    'remote': 'удалённая',
                    'hybrid': 'гибридная',
                    'office': 'офис',
                    'full-time': 'полная занятость',
                    'part-time': 'частичная занятость',
                }
            }
        }
        
        # Пропускаемые шаблоны (переменные, URL, технические термины)
        self.skip_patterns = [
            '%(', '%s', '%d', '{', '}', 'http://', 'https://', 'www.', '.com', '.org',
            'csrf', 'UTF-8', 'XML', 'JSON', 'API', 'URL', 'CSS', 'HTML', 'JS'
        ]

    def find_po_files(self):
        """Находит все .po файлы в проекте"""
        po_files = []
        for root, dirs, files in os.walk(project_root):
            for file in files:
                if file.endswith('.po') and 'locale' in root:
                    po_files.append(os.path.join(root, file))
        return po_files

    def get_language_from_path(self, po_file_path):
        """Определяет язык из пути к .po файлу"""
        path_parts = po_file_path.split(os.sep)
        for i, part in enumerate(path_parts):
            if part == 'locale':
                if i + 1 < len(path_parts):
                    return path_parts[i + 1]
        return None

    def should_skip_translation(self, text):
        """Определяет, нужно ли пропускать перевод текста"""
        if not text or len(text.strip()) <= 1:
            return True
            
        # Пропускаем переменные форматирования
        if any(pattern in text for pattern in self.skip_patterns):
            return True
            
        # Пропускаем одиночные слова без контекста (часто это имена полей)
        words = text.strip().split()
        if len(words) == 1 and len(text) < 20:
            return True
            
        # Пропускаем текст в верхнем регистре (часто это константы)
        if text.isupper():
            return True
            
        return False

    def check_glossary(self, text, target_lang):
        """Проверяет глоссарий для перевода"""
        text_lower = text.lower()
        for en_term, translation in self.glossary['en'][target_lang].items():
            if en_term in text_lower:
                # Заменяем термин в тексте, сохраняя регистр
                if en_term in text_lower:
                    return text_lower.replace(en_term, translation)
        return None

    def translate_google(self, text, target_lang):
        """Перевод через Google Translate"""
        try:
            time.sleep(0.1)  # Задержка чтобы не блокировали
            return GoogleTranslator(source='en', target=target_lang).translate(text)
        except Exception as e:
            print(f"    Google Translate ошибка: {e}")
            return None

    def translate_fallback(self, text, target_lang):
        """Резервный метод перевода через LibreTranslate"""
        try:
            # Используем LibreTranslate как fallback
            if target_lang == 'uz':
                target_lang = 'uz'  # LibreTranslate поддерживает узбекский
            elif target_lang == 'ru':
                target_lang = 'ru'
                
            url = "https://libretranslate.com/translate"
            payload = {
                'q': text,
                'source': 'en',
                'target': target_lang,
                'format': 'text'
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                return response.json()['translatedText']
        except Exception:
            pass
        return None

    def smart_translate(self, text, target_lang):
        """Умный перевод с использованием нескольких методов"""
        if self.should_skip_translation(text):
            self.skipped_count += 1
            return None
            
        # Сначала проверяем глоссарий
        glossary_translation = self.check_glossary(text, target_lang)
        if glossary_translation:
            return glossary_translation
            
        # Затем пробуем Google Translate
        translation = self.translate_google(text, target_lang)
        if translation:
            return translation
            
        # Fallback метод
        translation = self.translate_fallback(text, target_lang)
        if translation:
            return translation
            
        self.error_count += 1
        return None

    def translate_po_file(self, po_file_path, target_lang):
        """Переводит один .po файл с улучшенной логикой"""
        print(f"\n📁 Перевод файла: {os.path.basename(po_file_path)} -> {target_lang.upper()}")
        
        try:
            po = polib.pofile(po_file_path)
            untranslated_entries = [entry for entry in po if not entry.msgstr and entry.msgid]
            
            if not untranslated_entries:
                print(f"  ✅ Все строки уже переведены")
                return
                
            print(f"  📊 Найдено {len(untranslated_entries)} непереведенных строк")
            
            success_count = 0
            for i, entry in enumerate(untranslated_entries):
                if not entry.msgstr and entry.msgid:
                    translation = self.smart_translate(entry.msgid, target_lang)
                    if translation:
                        entry.msgstr = translation
                        success_count += 1
                        self.translated_count += 1
                        
                        if success_count % 25 == 0:
                            print(f"    🔄 Переведено {success_count}/{len(untranslated_entries)}...")
                            
                        # Показываем пример перевода каждые 50 строк
                        if success_count % 50 == 0:
                            short_text = entry.msgid[:60] + "..." if len(entry.msgid) > 60 else entry.msgid
                            short_trans = translation[:60] + "..." if len(translation) > 60 else translation
                            print(f"    📝 Пример: '{short_text}' -> '{short_trans}'")
            
            po.save(po_file_path)
            print(f"  ✅ Файл переведен: {success_count} новых переводов")
            print(f"  ⏭️  Пропущено: {len(untranslated_entries) - success_count} строк")
            
        except Exception as e:
            print(f"  ❌ Ошибка обработки файла: {e}")

    def create_po_files_if_missing(self):
        """Создает .po файлы если они отсутствуют"""
        print("🔍 Проверка наличия .po файлов...")
        
        created_count = 0
        for app in django.apps.apps.get_app_configs():
            app_path = Path(app.path)
            locale_path = app_path / 'locale'
            
            if locale_path.exists():
                for lang in self.target_languages:
                    lang_path = locale_path / lang / 'LC_MESSAGES'
                    po_file_path = lang_path / 'django.po'
                    
                    if not po_file_path.exists():
                        print(f"  📄 Создаем отсутствующий файл: {po_file_path}")
                        lang_path.mkdir(parents=True, exist_ok=True)
                        
                        po = polib.POFile()
                        po.metadata = {
                            'Project-Id-Version': '1.0',
                            'Report-Msgid-Bugs-To': '',
                            'POT-Creation-Date': '',
                            'PO-Revision-Date': '',
                            'Last-Translator': 'Auto Translator',
                            'Language-Team': '',
                            'Language': lang,
                            'MIME-Version': '1.0',
                            'Content-Type': 'text/plain; charset=utf-8',
                            'Content-Transfer-Encoding': '8bit',
                        }
                        po.save(str(po_file_path))
                        created_count += 1
        
        if created_count > 0:
            print(f"  ✅ Создано {created_count} новых .po файлов")
        else:
            print("  ✅ Все .po файлы присутствуют")

    def extract_translations(self):
        """Извлекает все строки для перевода из проекта"""
        print("\n🔧 Извлечение строк для перевода...")
        
        try:
            from django.core.management import call_command
            
            for lang in self.target_languages:
                print(f"  📝 Извлечение для языка: {lang.upper()}")
                call_command('makemessages', '-l', lang, '-a', '--ignore=venv/*', '--ignore=.venv/*', verbosity=0)
            
            print("  ✅ Строки для перевода извлечены")
            return True
            
        except Exception as e:
            print(f"  ❌ Ошибка извлечения строк: {e}")
            return False

    def compile_translations(self):
        """Компилирует переведенные .po файлы в .mo"""
        print("\n⚙️ Компиляция переводов...")
        
        try:
            from django.core.management import call_command
            
            call_command('compilemessages', '--ignore=venv/*', '--ignore=.venv/*', verbosity=0)
            print("  ✅ Переводы скомпилированы в .mo файлы")
            return True
            
        except Exception as e:
            print(f"  ❌ Ошибка компиляции: {e}")
            return False

    def get_translation_stats(self):
        """Получает подробную статистику по переводам"""
        print("\n" + "="*60)
        print("📊 ПОДРОБНАЯ СТАТИСТИКА ПЕРЕВОДА")
        print("="*60)
        
        po_files = self.find_po_files()
        total_translated = 0
        total_strings = 0
        
        for po_file in po_files:
            try:
                po = polib.pofile(po_file)
                lang = self.get_language_from_path(po_file)
                translated = len([e for e in po if e.msgstr])
                total = len(po)
                percentage = (translated / total) * 100 if total > 0 else 0
                
                total_translated += translated
                total_strings += total
                
                status = "✅ ХОРОШО" if percentage > 80 else "⚠️  НУЖНА РАБОТА" if percentage > 50 else "❌ ПЛОХО"
                
                print(f"\n🌐 {lang.upper()}: {os.path.basename(os.path.dirname(os.path.dirname(po_file)))}")
                print(f"   📈 Прогресс: {translated}/{total} ({percentage:.1f}%)")
                print(f"   🏷️  Статус: {status}")
                
            except Exception as e:
                print(f"   ❌ Ошибка чтения {po_file}: {e}")
        
        overall_percentage = (total_translated / total_strings) * 100 if total_strings > 0 else 0
        print(f"\n📈 ОБЩАЯ СТАТИСТИКА:")
        print(f"   Всего строк: {total_strings}")
        print(f"   Переведено: {total_translated}")
        print(f"   Общий прогресс: {overall_percentage:.1f}%")

    def save_glossary(self):
        """Сохраняет глоссарий в файл для ручного редактирования"""
        glossary_path = project_root / 'translation_glossary.json'
        with open(glossary_path, 'w', encoding='utf-8') as f:
            json.dump(self.glossary, f, ensure_ascii=False, indent=2)
        print(f"\n📖 Глоссарий сохранен в: {glossary_path}")

    def run(self):
        """Основной метод запуска перевода"""
        print("="*70)
        print("🚀 АВТОМАТИЧЕСКИЙ ПЕРЕВОД DJANGO ПРОЕКТА (УЛУЧШЕННАЯ ВЕРСИЯ)")
        print("="*70)
        print(f"🎯 Исходный язык: {self.source_language}")
        print(f"🌍 Целевые языки: {', '.join([lang.upper() for lang in self.target_languages])}")
        print("="*70)
        
        start_time = time.time()
        
        # Шаг 1: Создаем недостающие .po файлы
        self.create_po_files_if_missing()
        
        # Шаг 2: Извлекаем строки для перевода
        if not self.extract_translations():
            print("ℹ️  Продолжаем с существующими файлами...")
        
        # Шаг 3: Находим и переводим .po файлы
        po_files = self.find_po_files()
        print(f"\n📁 Найдено .po файлов: {len(po_files)}")
        
        for po_file in po_files:
            lang = self.get_language_from_path(po_file)
            if lang in self.target_languages:
                self.translate_po_file(po_file, lang)
        
        # Шаг 4: Компилируем переводы
        self.compile_translations()
        
        # Шаг 5: Сохраняем глоссарий
        self.save_glossary()
        
        # Шаг 6: Показываем статистику
        self.get_translation_stats()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "="*70)
        print("🎉 ПЕРЕВОД ЗАВЕРШЕН!")
        print("="*70)
        print(f"✅ Успешно переведено: {self.translated_count} строк")
        print(f"⏭️  Пропущено: {self.skipped_count} строк")
        print(f"❌ Ошибок перевода: {self.error_count}")
        print(f"⏱️  Затраченное время: {duration:.1f} секунд")
        print("\n💡 СОВЕТ: Проверьте файл translation_glossary.json")
        print("   и отредактируйте проблемные переводы вручную")
        print("="*70)

if __name__ == "__main__":
    # Проверяем зависимости
    try:
        import polib
        from deep_translator import GoogleTranslator
    except ImportError as e:
        print("❌ Установите необходимые зависимости:")
        print("   pip install polib deep-translator django requests")
        sys.exit(1)
    
    # Запускаем перевод
    try:
        translator = AdvancedProjectTranslator()
        translator.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Перевод прерван пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")
        sys.exit(1)