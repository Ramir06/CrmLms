#!/usr/bin/env python
"""Исправленная загрузка .env с полной очисткой от Windows символов"""
import os
from pathlib import Path

def load_env_cleanly(env_path):
    """Загружает .env файл с полной очисткой от проблемных символов"""
    if not env_path.exists():
        print(f"❌ Файл {env_path} не найден")
        return
    
    print(f"🔄 Загрузка {env_path} с очисткой...")
    
    # Читаем файл в бинарном режиме для точного контроля
    with open(env_path, 'rb') as f:
        raw_content = f.read()
    
    print(f"📊 Размер файла: {len(raw_content)} байт")
    
    # Декодируем с обработкой ошибок
    try:
        content = raw_content.decode('utf-8')
        print("✅ UTF-8 декодирование успешно")
    except UnicodeDecodeError as e:
        print(f"⚠️ Ошибка UTF-8: {e}")
        # Пробуем Latin-1 как запасной вариант
        content = raw_content.decode('latin-1')
        print("✅ Использовано Latin-1 декодирование")
    
    # Очищаем каждую строку
    cleaned_lines = []
    for line_num, line in enumerate(content.split('\n'), 1):
        original = line
        # Удаляем все виды переносов строк и пробелы
        cleaned = line.strip().replace('\r', '').replace('\n', '')
        
        if cleaned:  # Пропускаем пустые строки
            cleaned_lines.append(cleaned)
            
            # Показываем изменения
            if original != cleaned:
                print(f"  Строка {line_num}: {repr(original)} -> {repr(cleaned)}")
    
    # Устанавливаем переменные окружения
    env_vars = {}
    for line in cleaned_lines:
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            env_vars[key] = value
            os.environ[key] = value
            print(f"  ✅ {key} = {repr(value)}")
    
    print(f"✅ Загружено {len(env_vars)} переменных окружения")
    return env_vars

if __name__ == "__main__":
    # Тест загрузки
    env_path = Path(__file__).resolve().parent / '.env'
    load_env_cleanly(env_path)
    
    # Проверка переменных
    print("\n🔍 Проверка переменных окружения:")
    db_vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT']
    for var in db_vars:
        value = os.environ.get(var, 'не установлена')
        print(f"{var}: {repr(value)}")
