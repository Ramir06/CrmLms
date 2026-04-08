#!/usr/bin/env python
"""Проверка .env файла на скрытые символы"""
import os
from pathlib import Path

# Путь к .env файлу
env_path = Path(__file__).resolve().parent / '.env'

print(f"Проверка файла: {env_path}")
print(f"Файл существует: {env_path.exists()}")
print()

if env_path.exists():
    with open(env_path, 'rb') as f:
        content = f.read()
    
    print("=== Анализ байтов файла ===")
    print(f"Размер файла: {len(content)} байт")
    print(f"Кодировка: {content[:100]!r}")  # первые 100 байт
    print()
    
    # Декодируем с обработкой ошибок
    try:
        decoded = content.decode('utf-8')
        print("✅ Успешное декодирование UTF-8")
    except UnicodeDecodeError as e:
        print(f"❌ Ошибка декодирования: {e}")
        # Пробуем декодировать с заменой ошибок
        decoded = content.decode('utf-8', errors='replace')
        print("⚠️ Декодировано с заменой ошибочных символов")
    
    print()
    print("=== Поиск скрытых символов ===")
    
    # Ищем специфичные символы
    hidden_chars = []
    for i, char in enumerate(decoded):
        code = ord(char)
        if code in [0xFEFF, 0xFFFE]:  # BOM
            hidden_chars.append(f"BOM (0x{code:04X}) на позиции {i}")
        elif code == 0xC2 and i+1 < len(decoded) and ord(decoded[i+1]) in range(0x80, 0xA0):
            hidden_chars.append(f"Символ 0xC2... на позиции {i}")
        elif code in [0x00, 0x0B, 0x0C]:  # Control characters
            hidden_chars.append(f"Control char (0x{code:02X}) на позиции {i}")
        elif char in ['\ufeff']:  # Zero-width space
            hidden_chars.append(f"Zero-width space на позиции {i}")
    
    if hidden_chars:
        print("❌ Найдены скрытые символы:")
        for char_info in hidden_chars:
            print(f"  - {char_info}")
    else:
        print("✅ Скрытые символы не найдены")
    
    print()
    print("=== Строки с repr() ===")
    lines = decoded.split('\n')
    for i, line in enumerate(lines, 1):
        if line.strip():  # пропускаем пустые строки
            print(f"Строка {i}: {repr(line)}")
            
            # Проверка на специфичные проблемы
            if '\ufeff' in line:
                print(f"  ⚠️ BOM в строке {i}")
            if line.endswith('\r'):
                print(f"  ⚠️ Windows перенос строки в строке {i}")
            if line.startswith(' ') or line.endswith(' '):
                print(f"  ⚠️ Пробелы в начале/конце строки {i}")
else:
    print("❌ Файл .env не найден!")
