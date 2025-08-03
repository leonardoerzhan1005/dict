from django import template
from django.utils.html import strip_tags
import re

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Получить значение из словаря по ключу"""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def get_translation(obj, language_code):
    """Получить перевод объекта для указанного языка"""
    if hasattr(obj, 'translations'):
        try:
            return obj.translations.get(language__code=language_code)
        except:
            return None
    return None

@register.filter
def get_translation_name(obj, language_code):
    """Получить название перевода объекта для указанного языка"""
    translation = get_translation(obj, language_code)
    if translation:
        return translation.name
    return obj.code if hasattr(obj, 'code') else str(obj)

@register.filter
def get_translation_description(obj, language_code):
    """Получить описание перевода объекта для указанного языка"""
    translation = get_translation(obj, language_code)
    if translation and hasattr(translation, 'description'):
        return translation.description
    return ''

@register.filter
def has_translation(obj, language_code):
    """Проверить, есть ли перевод для указанного языка"""
    return get_translation(obj, language_code) is not None

@register.filter
def get_missing_languages(obj, all_languages):
    """Получить список языков, для которых нет переводов"""
    if not hasattr(obj, 'translations'):
        return all_languages
    
    existing_languages = set(obj.translations.values_list('language__code', flat=True))
    return [lang for lang in all_languages if lang.code not in existing_languages]

@register.filter
def get_translation_percentage(obj, all_languages):
    """Получить процент переведенных языков"""
    if not hasattr(obj, 'translations'):
        return 0
    
    total_languages = all_languages.count()
    translated_languages = obj.translations.count()
    
    if total_languages == 0:
        return 0
    
    return round((translated_languages / total_languages) * 100)

@register.filter
def truncatewords_html(value, arg):
    """
    Обрезает HTML контент до указанного количества слов, сохраняя HTML теги
    """
    try:
        length = int(arg)
    except ValueError:
        return value
    
    if not value:
        return value
    
    # Сначала получаем чистый текст без HTML тегов
    text_only = strip_tags(value)
    
    # Разбиваем на слова
    words = text_only.split()
    
    if len(words) <= length:
        return value
    
    # Обрезаем до нужного количества слов
    truncated_words = words[:length]
    truncated_text = ' '.join(truncated_words)
    
    # Добавляем многоточие
    truncated_text += '...'
    
    return truncated_text 