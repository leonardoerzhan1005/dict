#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dictionary_django.settings')
django.setup()

from dictionary.models import Word, Language, Category, Tag

def create_legal_term_cycle():
    """Создает один юридический термин 100 раз через цикл"""
    
    # Получаем или создаем необходимые объекты
    language = Language.objects.get(code='ru')
    
    # Создаем категорию для юридических терминов
    category, created = Category.objects.get_or_create(code='legal_terms')
    if created:
        print(f"Создана новая категория: {category}")
    
    # Создаем теги
    legal_tag, created = Tag.objects.get_or_create(code='legal')
    if created:
        print(f"Создан новый тег: {legal_tag}")
    
    noun_tag, created = Tag.objects.get_or_create(code='noun')
    if created:
        print(f"Создан новый тег: {noun_tag}")
    
    # Определяем юридический термин с длинным названием
    legal_term = "Конституционно-правовой институт административно"
    
    legal_meaning = """Комплексная система правовых норм, регулирующих порядок рассмотрения и разрешения дел об административных правонарушениях в области дорожного движения, включающая в себя совокупность конституционных принципов, административно-процессуальных норм, материальных норм административного права, а также норм, регулирующих деятельность органов государственной власти и местного самоуправления, их должностных лиц по применению мер административного принуждения в целях обеспечения безопасности дорожного движения, защиты прав и законных интересов граждан, юридических лиц, общества и государства от противоправных посягательств в указанной сфере общественных отношений."""
    
    print(f"Начинаем создание термина: {legal_term}")
    print(f"Будет создано 100 записей...")
    
    # Цикл создания 100 записей
    for i in range(1, 101):
        # Создаем уникальное слово, добавляя номер
        unique_word = f"{legal_term} (версия {i})"
        
        word = Word.objects.create(
            word=unique_word,
            language=language,
            meaning=legal_meaning,
            category=category,
            pronunciation=f'[]',
            difficulty='hard',
            status='approved'
        )
        
        # Добавляем теги
        word.tags.add(legal_tag, noun_tag)
        
        if i % 10 == 0:
            print(f"Создано записей: {i}")
    
    print(f"Готово! Создано {i} записей юридического термина.")
    
    # Показываем статистику
    total_words = Word.objects.filter(category=category).count()
    print(f"Всего юридических терминов в базе: {total_words}")

if __name__ == '__main__':
    create_legal_term_cycle() 