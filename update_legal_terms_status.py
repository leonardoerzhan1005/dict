#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dictionary_django.settings')
django.setup()

from dictionary.models import Word, Category

def update_legal_terms_status():
    """Обновляет статус всех юридических терминов на 'approved'"""
    
    # Находим все юридические термины
    legal_words = Word.objects.filter(category__code='legal_terms')
    
    print(f"Найдено {legal_words.count()} юридических терминов")
    
    # Обновляем статус на 'approved'
    updated_count = legal_words.update(status='approved')
    
    print(f"Обновлено {updated_count} записей - статус изменен на 'опубликовано'")
    
    # Проверяем результат
    approved_words = Word.objects.filter(category__code='legal_terms', status='approved')
    print(f"Всего опубликованных юридических терминов: {approved_words.count()}")

if __name__ == '__main__':
    update_legal_terms_status() 