import os
from pathlib import Path
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Find template files that are not referenced in code and optionally move them to templates/archived_unused"

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Actually move detected unused templates into templates/archived_unused/",
        )

    def handle(self, *args, **options):
        base = Path(__file__).resolve().parents[4]
        templates = []
        for root, dirs, files in os.walk(base):
            if os.path.sep + 'templates' + os.path.sep in root or root.endswith(os.path.sep + 'templates'):
                for f in files:
                    if f.endswith('.html'):
                        templates.append(Path(root) / f)

        self.stdout.write(f"Found {len(templates)} template files to check")

        code_files = []
        for root, dirs, files in os.walk(base):
            for f in files:
                if f.endswith(('.py', '.html', '.js')):
                    code_files.append(Path(root) / f)

        unused = []
        for tpl in templates:
            name = tpl.name
            found = False
            for cf in code_files:
                try:
                    text = cf.read_text(encoding='utf-8')
                except Exception:
                    continue
                if name in text:
                    found = True
                    break
            if not found:
                unused.append(tpl)

        if not unused:
            self.stdout.write("No unused templates detected.")
            return

        self.stdout.write("Unused templates:")
        for u in unused:
            self.stdout.write(str(u))

        if options['apply']:
            archive = base / 'templates' / 'archived_unused'
            archive.mkdir(parents=True, exist_ok=True)
            for u in unused:
                target = archive / u.name
                try:
                    u.rename(target)
                    self.stdout.write(f"Moved {u} -> {target}")
                except Exception as e:
                    self.stderr.write(f"Failed to move {u}: {e}")
            self.stdout.write("Archived unused templates.")
        else:
            self.stdout.write("Run with --apply to move these files to templates/archived_unused/")
