#!/usr/bin/env python3
"""
Скрипт для установки зависимостей переводчика
"""

import subprocess
import sys

def install_dependencies():
    packages = [
        'polib>=1.1',
        'deep-translator>=1.11',
        'requests>=2.25',
        'Django>=3.2'
    ]
    
    print("Установка зависимостей для переводчика...")
    
    for package in packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✅ {package} установлен")
        except subprocess.CalledProcessError:
            print(f"❌ Ошибка установки {package}")
    
    print("\n🎉 Все зависимости установлены!")

if __name__ == "__main__":
    install_dependencies()