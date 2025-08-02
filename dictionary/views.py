from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Category, CategoryTranslation, Tag, TagTranslation, Language, InterfaceTranslation, Word, Translation, CustomUser
from .forms import CustomUserCreationForm, WordForm, WordTranslationForm
import json

def home(request):
    """Главная страница с поиском слов"""
    # Получить параметры поиска
    query = request.GET.get('q', '').strip()
    language_code = request.GET.get('lang', '')
    category_id = request.GET.get('category', '')
    page = request.GET.get('page', 1)
    try:
        page = int(page)
    except ValueError:
        page = 1
    
    # Преобразуем category_id в int, если он не пустой
    try:
        category_id = int(category_id) if category_id else None
    except ValueError:
        category_id = None
    
    # Базовый queryset - только одобренные и не удалённые слова
    words = Word.objects.filter(status='approved', is_deleted=False)
    
    # Фильтр по языку
    if language_code:
        words = words.filter(language__code=language_code)
    
    # Фильтр по категории
    if category_id is not None:
        words = words.filter(category_id=category_id)
    
    # Поиск по запросу
    if query:
        # Поиск по слову и значению на всех языках
        search_query = Q(word__icontains=query) | Q(meaning__icontains=query)
        words = words.filter(search_query)
    
    # Сортировка
    words = words.order_by('word')
    
    # Пагинация
    paginator = Paginator(words, 20)  # 20 слов на страницу
    words_page = paginator.get_page(page)
    
    # Получить данные для фильтров
    languages = Language.objects.all().order_by('code')
    categories = Category.objects.all().order_by('code')
    
    # Получить переводы названий категорий
    user_language = request.session.get('language', 'ru')
    categories_with_translations = []
    for category in categories:
        try:
            translation = CategoryTranslation.objects.get(
                category=category, 
                language__code=user_language
            )
            categories_with_translations.append({
                'category': category,
                'name': translation.name
            })
        except CategoryTranslation.DoesNotExist:
            categories_with_translations.append({
                'category': category,
                'name': category.code
            })
    
    context = {
        'words': words_page,
        'languages': languages,
        'categories': categories_with_translations,
        'current_query': query,
        'current_language': language_code,
        'current_category': category_id,
        'user_language': user_language,
    }
    
    return render(request, 'dictionary/home.html', context)

def word_detail(request, word_id):
    """Детальная страница слова с переводами"""
    word = get_object_or_404(Word, id=word_id, status='approved', is_deleted=False)
    
    # Получить все переводы слова
    translations = word.from_translations.all().select_related('to_word', 'to_word__language')
    
    # Получить примеры
    examples = word.examples.all()
    
    # Получить теги с переводами
    user_language = request.session.get('language', 'ru')
    tags_with_translations = []
    for tag in word.tags.all():
        try:
            translation = TagTranslation.objects.get(
                tag=tag, 
                language__code=user_language
            )
            tags_with_translations.append({
                'tag': tag,
                'name': translation.name
            })
        except TagTranslation.DoesNotExist:
            tags_with_translations.append({
                'tag': tag,
                'name': tag.code
            })
    
    context = {
        'word': word,
        'translations': translations,
        'examples': examples,
        'tags': tags_with_translations,
        'user_language': user_language,
    }
    
    return render(request, 'dictionary/word_detail.html', context)

def user_login(request):
    """Представление для входа пользователя"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('dictionary:home')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    
    return render(request, 'dictionary/login.html')

def user_logout(request):
    """Представление для выхода пользователя"""
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('dictionary:home')

def user_register(request):
    """Представление для регистрации пользователя"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Аккаунт создан для {user.username}!')
            return redirect('dictionary:home')
        else:
            messages.error(request, 'Ошибка при создании аккаунта. Проверьте данные.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'dictionary/register.html', {'form': form})

@login_required
def user_profile(request):
    """Представление для профиля пользователя"""
    return render(request, 'dictionary/profile.html')

@staff_member_required
def translation_dashboard(request):
    """Дашборд для управления переводами"""
    languages = Language.objects.all().order_by('code')
    categories = Category.objects.all().order_by('code')
    tags = Tag.objects.all().order_by('code')
    
    # Получаем статистику переводов
    category_stats = {}
    for category in categories:
        translations = category.translations.all()
        total_languages = languages.count()
        translated_languages = translations.count()
        category_stats[category.id] = {
            'total': total_languages,
            'translated': translated_languages,
            'percentage': round((translated_languages / total_languages) * 100) if total_languages > 0 else 0
        }
    
    tag_stats = {}
    for tag in tags:
        translations = tag.translations.all()
        total_languages = languages.count()
        translated_languages = translations.count()
        tag_stats[tag.id] = {
            'total': total_languages,
            'translated': translated_languages,
            'percentage': round((translated_languages / total_languages) * 100) if total_languages > 0 else 0
        }
    
    # Общая статистика
    total_categories = categories.count()
    total_tags = tags.count()
    total_languages = languages.count()
    
    # Категории с полными переводами
    fully_translated_categories = sum(1 for stats in category_stats.values() if stats['percentage'] == 100)
    fully_translated_tags = sum(1 for stats in tag_stats.values() if stats['percentage'] == 100)
    
    # Категории без переводов
    untranslated_categories = sum(1 for stats in category_stats.values() if stats['percentage'] == 0)
    untranslated_tags = sum(1 for stats in tag_stats.values() if stats['percentage'] == 0)
    
    context = {
        'languages': languages,
        'categories': categories,
        'tags': tags,
        'category_stats': category_stats,
        'tag_stats': tag_stats,
        'total_categories': total_categories,
        'total_tags': total_tags,
        'total_languages': total_languages,
        'fully_translated_categories': fully_translated_categories,
        'fully_translated_tags': fully_translated_tags,
        'untranslated_categories': untranslated_categories,
        'untranslated_tags': untranslated_tags,
    }
    return render(request, 'dictionary/translation_dashboard.html', context)

@staff_member_required
def category_translations_edit(request, category_id):
    """Редактирование переводов категории"""
    category = get_object_or_404(Category, id=category_id)
    languages = Language.objects.all().order_by('code')
    
    if request.method == 'POST':
        with transaction.atomic():
            for language in languages:
                name = request.POST.get(f'name_{language.code}')
                description = request.POST.get(f'description_{language.code}')
                
                if name:  # Сохраняем только если есть название
                    translation, created = CategoryTranslation.objects.get_or_create(
                        category=category,
                        language=language,
                        defaults={'name': name, 'description': description or ''}
                    )
                    if not created:
                        translation.name = name
                        translation.description = description or ''
                        translation.save()
        
        messages.success(request, f'Переводы для категории "{category.code}" обновлены')
        return redirect('dictionary:translation_dashboard')
    
    # Получаем существующие переводы
    translations = {}
    for translation in category.translations.all():
        translations[translation.language.code] = {
            'name': translation.name,
            'description': translation.description
        }
    
    context = {
        'category': category,
        'languages': languages,
        'translations': translations,
    }
    return render(request, 'dictionary/category_translations_edit.html', context)

@staff_member_required
def tag_translations_edit(request, tag_id):
    """Редактирование переводов тега"""
    tag = get_object_or_404(Tag, id=tag_id)
    languages = Language.objects.all().order_by('code')
    
    if request.method == 'POST':
        with transaction.atomic():
            for language in languages:
                name = request.POST.get(f'name_{language.code}')
                
                if name:  # Сохраняем только если есть название
                    translation, created = TagTranslation.objects.get_or_create(
                        tag=tag,
                        language=language,
                        defaults={'name': name}
                    )
                    if not created:
                        translation.name = name
                        translation.save()
        
        messages.success(request, f'Переводы для тега "{tag.code}" обновлены')
        return redirect('dictionary:translation_dashboard')
    
    # Получаем существующие переводы
    translations = {}
    for translation in tag.translations.all():
        translations[translation.language.code] = {
            'name': translation.name
        }
    
    context = {
        'tag': tag,
        'languages': languages,
        'translations': translations,
    }
    return render(request, 'dictionary/tag_translations_edit.html', context)

@staff_member_required
def interface_translations_edit(request):
    """Редактирование переводов интерфейса"""
    languages = Language.objects.all().order_by('code')
    
    if request.method == 'POST':
        with transaction.atomic():
            # Получаем все ключи из формы
            keys = set()
            for key in request.POST.keys():
                if key.startswith('value_'):
                    lang_code = key.split('_')[1]
                    keys.add(lang_code)
            
            for key in keys:
                for language in languages:
                    value = request.POST.get(f'value_{key}_{language.code}')
                    if value is not None:  # Сохраняем даже пустые значения
                        translation, created = InterfaceTranslation.objects.get_or_create(
                            language=language,
                            key=key,
                            defaults={'value': value}
                        )
                        if not created:
                            translation.value = value
                            translation.save()
        
        messages.success(request, 'Переводы интерфейса обновлены')
        return redirect('dictionary:translation_dashboard')
    
    # Получаем все ключи переводов
    all_keys = set(InterfaceTranslation.objects.values_list('key', flat=True))
    
    # Получаем существующие переводы
    translations = {}
    for key in all_keys:
        translations[key] = {}
        for language in languages:
            try:
                translation = InterfaceTranslation.objects.get(language=language, key=key)
                translations[key][language.code] = translation.value
            except InterfaceTranslation.DoesNotExist:
                translations[key][language.code] = ''
    
    context = {
        'languages': languages,
        'translations': translations,
    }
    return render(request, 'dictionary/interface_translations_edit.html', context)

@require_http_methods(["POST"])
@staff_member_required
def add_missing_translations(request):
    """API для добавления недостающих переводов"""
    translation_type = request.POST.get('type')
    item_id = request.POST.get('id')
    
    if translation_type == 'category':
        category = get_object_or_404(Category, id=item_id)
        all_languages = Language.objects.all()
        existing_languages = set(category.translations.values_list('language__code', flat=True))
        missing_languages = [lang for lang in all_languages if lang.code not in existing_languages]
        
        created_count = 0
        for lang in missing_languages:
            CategoryTranslation.objects.create(
                category=category,
                language=lang,
                name=f"[{lang.code}] {category.code}",
                description=""
            )
            created_count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'Создано {created_count} недостающих переводов',
            'created_count': created_count
        })
    
    elif translation_type == 'tag':
        tag = get_object_or_404(Tag, id=item_id)
        all_languages = Language.objects.all()
        existing_languages = set(tag.translations.values_list('language__code', flat=True))
        missing_languages = [lang for lang in all_languages if lang.code not in existing_languages]
        
        created_count = 0
        for lang in missing_languages:
            TagTranslation.objects.create(
                tag=tag,
                language=lang,
                name=f"[{lang.code}] {tag.code}"
            )
            created_count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'Создано {created_count} недостающих переводов',
            'created_count': created_count
        })
    
    return JsonResponse({'success': False, 'message': 'Неизвестный тип перевода'})

@staff_member_required
def bulk_add_missing_translations(request):
    """Массовое добавление недостающих переводов"""
    if request.method == 'POST':
        translation_type = request.POST.get('type')
        created_count = 0
        
        if translation_type == 'categories':
            categories = Category.objects.all()
            all_languages = Language.objects.all()
            
            for category in categories:
                existing_languages = set(category.translations.values_list('language__code', flat=True))
                missing_languages = [lang for lang in all_languages if lang.code not in existing_languages]
                
                for lang in missing_languages:
                    CategoryTranslation.objects.create(
                        category=category,
                        language=lang,
                        name=f"[{lang.code}] {category.code}",
                        description=""
                    )
                    created_count += 1
        
        elif translation_type == 'tags':
            tags = Tag.objects.all()
            all_languages = Language.objects.all()
            
            for tag in tags:
                existing_languages = set(tag.translations.values_list('language__code', flat=True))
                missing_languages = [lang for lang in all_languages if lang.code not in existing_languages]
                
                for lang in missing_languages:
                    TagTranslation.objects.create(
                        tag=tag,
                        language=lang,
                        name=f"[{lang.code}] {tag.code}"
                    )
                    created_count += 1
        
        messages.success(request, f'Создано {created_count} недостающих переводов')
        return redirect('dictionary:translation_dashboard')
    
    return redirect('dictionary:translation_dashboard')

@staff_member_required
def translation_progress(request):
    """Страница с прогрессом переводов"""
    languages = Language.objects.all().order_by('code')
    categories = Category.objects.all().order_by('code')
    tags = Tag.objects.all().order_by('code')
    
    # Статистика по языкам
    language_stats = {}
    for language in languages:
        category_translations = CategoryTranslation.objects.filter(language=language).count()
        tag_translations = TagTranslation.objects.filter(language=language).count()
        interface_translations = InterfaceTranslation.objects.filter(language=language).count()
        
        total_items = categories.count() + tags.count()
        total_translations = category_translations + tag_translations
        
        language_stats[language.code] = {
            'language': language,
            'category_translations': category_translations,
            'tag_translations': tag_translations,
            'interface_translations': interface_translations,
            'total_items': total_items,
            'total_translations': total_translations,
            'percentage': round((total_translations / total_items) * 100) if total_items > 0 else 0
        }
    
    context = {
        'languages': languages,
        'categories': categories,
        'tags': tags,
        'language_stats': language_stats,
    }
    return render(request, 'dictionary/translation_progress.html', context)

@staff_member_required
def word_translations_dashboard(request):
    """Дашборд для управления переводами слов"""
    # Получить параметры поиска
    query = request.GET.get('q', '').strip()
    source_language = request.GET.get('source_lang', '')
    target_language = request.GET.get('target_lang', '')
    category_id = request.GET.get('category', '')
    status = request.GET.get('status', '')
    page = request.GET.get('page', 1)
    
    # Базовый queryset
    words = Word.objects.filter(is_deleted=False)
    
    # Фильтр по исходному языку
    if source_language:
        words = words.filter(language__code=source_language)
    
    # Фильтр по категории
    if category_id:
        words = words.filter(category_id=category_id)
    
    # Поиск по запросу
    if query:
        search_query = Q(word__icontains=query) | Q(meaning__icontains=query)
        words = words.filter(search_query)
    
    # Фильтр по статусу перевода
    if status == 'translated':
        words = words.filter(from_translations__isnull=False).distinct()
    elif status == 'untranslated':
        words = words.filter(from_translations__isnull=True)
    
    # Сортировка
    words = words.order_by('word')
    
    # Пагинация
    paginator = Paginator(words, 20)
    words_page = paginator.get_page(page)
    
    # Получить данные для фильтров
    languages = Language.objects.all().order_by('code')
    categories = Category.objects.all().order_by('code')
    
    # Статистика
    total_words = words.count()
    translated_words = words.filter(from_translations__isnull=False).distinct().count()
    untranslated_words = total_words - translated_words
    
    context = {
        'words': words_page,
        'languages': languages,
        'categories': categories,
        'current_query': query,
        'current_source_lang': source_language,
        'current_target_lang': target_language,
        'current_category': category_id,
        'current_status': status,
        'total_words': total_words,
        'translated_words': translated_words,
        'untranslated_words': untranslated_words,
    }
    return render(request, 'dictionary/word_translations_dashboard.html', context)

@staff_member_required
def word_translation_edit(request, word_id):
    """Редактирование переводов конкретного слова"""
    word = get_object_or_404(Word, id=word_id, is_deleted=False)
    languages = Language.objects.all().order_by('code')
    
    if request.method == 'POST':
        with transaction.atomic():
            # Обработка переводов
            for language in languages:
                if language.id != word.language.id:  # Не переводим на тот же язык
                    translation_word = request.POST.get(f'translation_word_{language.code}')
                    translation_meaning = request.POST.get(f'translation_meaning_{language.code}')
                    note = request.POST.get(f'note_{language.code}', '')
                    
                    if translation_word:  # Сохраняем только если есть перевод
                        # Создаем или получаем слово на целевом языке
                        target_word, created = Word.objects.get_or_create(
                            word=translation_word,
                            language=language,
                            category=word.category,
                            defaults={
                                'meaning': translation_meaning or '',
                                'status': 'pending',
                                'is_deleted': False
                            }
                        )
                        
                        if not created:
                            target_word.meaning = translation_meaning or ''
                            target_word.save()
                        
                        # Создаем или обновляем перевод
                        translation, created = Translation.objects.get_or_create(
                            from_word=word,
                            to_word=target_word,
                            defaults={'note': note, 'status': 'pending', 'order': 1}
                        )
                        
                        if not created:
                            translation.note = note
                            translation.save()
        
        messages.success(request, f'Переводы для слова "{word.word}" обновлены')
        return redirect('dictionary:word_translations_dashboard')
    
    # Получить существующие переводы
    existing_translations = {}
    for translation in word.from_translations.all():
        existing_translations[translation.to_word.language.code] = {
            'word': translation.to_word.word,
            'meaning': translation.to_word.meaning,
            'note': translation.note
        }
    
    context = {
        'word': word,
        'languages': languages,
        'existing_translations': existing_translations,
    }
    return render(request, 'dictionary/word_translation_edit.html', context)

@staff_member_required
def bulk_word_translation(request):
    """Массовое редактирование переводов слов"""
    # Получить параметры
    source_language = request.GET.get('source_lang', '')
    target_language = request.GET.get('target_lang', '')
    category_id = request.GET.get('category', '')
    
    if request.method == 'POST':
        # Обработка массового перевода
        word_ids = request.POST.getlist('word_ids')
        translations_data = request.POST.get('translations_data', '')
        
        if word_ids and translations_data:
            try:
                translations = json.loads(translations_data)
                created_count = 0
                
                with transaction.atomic():
                    for word_id in word_ids:
                        word = Word.objects.get(id=word_id)
                        if str(word_id) in translations:
                            target_lang_code = translations[str(word_id)]['target_lang']
                            translation_text = translations[str(word_id)]['translation']
                            
                            if translation_text:
                                target_language = Language.objects.get(code=target_lang_code)
                                
                                # Создаем или получаем слово на целевом языке
                                target_word, created = Word.objects.get_or_create(
                                    word=translation_text,
                                    language=target_language,
                                    category=word.category,
                                    defaults={
                                        'meaning': '',
                                        'status': 'pending',
                                        'is_deleted': False
                                    }
                                )
                                
                                # Создаем перевод
                                translation, created = Translation.objects.get_or_create(
                                    from_word=word,
                                    to_word=target_word,
                                    defaults={'status': 'pending', 'order': 1}
                                )
                                
                                if created:
                                    created_count += 1
                
                messages.success(request, f'Создано {created_count} новых переводов')
            except Exception as e:
                messages.error(request, f'Ошибка при сохранении переводов: {str(e)}')
        
        return redirect('dictionary:word_translations_dashboard')
    
    # Получить слова для перевода
    words = Word.objects.filter(is_deleted=False)
    
    if source_language:
        words = words.filter(language__code=source_language)
    
    if category_id:
        words = words.filter(category_id=category_id)
    
    # Исключаем слова, которые уже имеют переводы на целевой язык
    if target_language:
        target_lang = Language.objects.get(code=target_language)
        words = words.exclude(
            from_translations__to_word__language=target_lang
        )
    
    words = words.order_by('word')[:50]  # Ограничиваем для производительности
    
    # Получить данные для фильтров
    languages = Language.objects.all().order_by('code')
    categories = Category.objects.all().order_by('code')
    
    context = {
        'words': words,
        'languages': languages,
        'categories': categories,
        'source_language': source_language,
        'target_language': target_language,
        'category_id': category_id,
    }
    return render(request, 'dictionary/bulk_word_translation.html', context)

@staff_member_required
def translation_search(request):
    """Поиск переводов с автодополнением"""
    query = request.GET.get('q', '').strip()
    source_lang = request.GET.get('source_lang', '')
    target_lang = request.GET.get('target_lang', '')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX запрос для автодополнения
        if query:
            words = Word.objects.filter(
                word__icontains=query,
                is_deleted=False
            )
            
            if source_lang:
                words = words.filter(language__code=source_lang)
            
            suggestions = []
            for word in words[:10]:
                suggestions.append({
            'id': word.id,
            'word': word.word,
                    'meaning': word.meaning,
            'language': word.language.code,
                    'category': word.category.code if word.category else ''
                })
            
            return JsonResponse({'suggestions': suggestions})
    
    # Обычный поиск
    words = Word.objects.filter(is_deleted=False)
    
    if query:
        search_query = Q(word__icontains=query) | Q(meaning__icontains=query)
        words = words.filter(search_query)
    
    if source_lang:
        words = words.filter(language__code=source_lang)
    
    words = words.order_by('word')
    
    context = {
        'words': words,
        'query': query,
        'source_lang': source_lang,
        'target_lang': target_lang,
        'languages': Language.objects.all().order_by('code'),
    }
    return render(request, 'dictionary/translation_search.html', context)

@staff_member_required
def multi_translate_word(request, word_id):
    """Мультиперевод одного слова на несколько языков одновременно"""
    word = get_object_or_404(Word, id=word_id, is_deleted=False)
    languages = Language.objects.all().order_by('code')
    
    if request.method == 'POST':
        # Получаем выбранные языки для перевода
        target_languages = request.POST.getlist('target_languages')
        translations_data = request.POST.get('translations_data', '')
        
        if target_languages and translations_data:
            try:
                translations = json.loads(translations_data)
                created_count = 0
                
                with transaction.atomic():
                    for lang_code in target_languages:
                        if lang_code in translations and translations[lang_code].strip():
                            target_language = Language.objects.get(code=lang_code)
                            translation_text = translations[lang_code].strip()
                            
                            # Создаем или получаем слово на целевом языке
                            target_word, created = Word.objects.get_or_create(
                                word=translation_text,
                                language=target_language,
                                category=word.category,
                                defaults={
                                    'meaning': word.meaning,  # Копируем значение
                                    'status': 'pending',
                                    'is_deleted': False
                                }
                            )
                            
                            if not created:
                                target_word.meaning = word.meaning
                                target_word.save()
                            
                            # Создаем перевод
                            translation, created = Translation.objects.get_or_create(
                                from_word=word,
                                to_word=target_word,
                                defaults={'status': 'pending', 'order': 1}
                            )
                            
                            if created:
                                created_count += 1
                
                messages.success(request, f'Создано {created_count} новых переводов для слова "{word.word}"')
                return redirect('dictionary:word_translations_dashboard')
                
            except Exception as e:
                messages.error(request, f'Ошибка при сохранении переводов: {str(e)}')
    
    # Получить существующие переводы
    existing_translations = {}
    for translation in word.from_translations.all():
        existing_translations[translation.to_word.language.code] = translation.to_word.word
    
    # Получить доступные языки для перевода (исключая исходный и уже переведенные)
    available_languages = []
    for language in languages:
        if language.id != word.language.id and language.code not in existing_translations:
            available_languages.append(language)
    
    context = {
        'word': word,
        'languages': languages,
        'available_languages': available_languages,
        'existing_translations': existing_translations,
    }
    return render(request, 'dictionary/multi_translate_word.html', context)

@staff_member_required
def bulk_multi_translate(request):
    """Массовый мультиперевод - перевод множества слов на несколько языков"""
    if request.method == 'POST':
        word_ids = request.POST.getlist('word_ids')
        target_languages = request.POST.getlist('target_languages')
        translations_data = request.POST.get('translations_data', '')
        
        if word_ids and target_languages and translations_data:
            try:
                translations = json.loads(translations_data)
                created_count = 0
                updated_count = 0
                
                with transaction.atomic():
                    for word_id in word_ids:
                        word = Word.objects.get(id=word_id)
                        
                        for lang_code in target_languages:
                            key = f"{word_id}_{lang_code}"
                            if key in translations and translations[key].strip():
                                target_language = Language.objects.get(code=lang_code)
                                translation_text = translations[key].strip()
                                
                                # Проверяем, существует ли уже слово с таким переводом
                                existing_word = Word.objects.filter(
                                    word=translation_text,
                                    language=target_language,
                                    is_deleted=False
                                ).first()
                                
                                if existing_word:
                                    # Используем существующее слово
                                    target_word = existing_word
                                else:
                                    # Создаем новое слово на целевом языке
                                    target_word, created = Word.objects.get_or_create(
                                        word=translation_text,
                                        language=target_language,
                                        category=word.category,
                                        defaults={
                                            'meaning': word.meaning,
                                            'status': 'pending',
                                            'is_deleted': False,
                                            'created_by': request.user
                                        }
                                    )
                                    if created:
                                        created_count += 1
                                
                                # Создаем или обновляем перевод
                                translation, created = Translation.objects.get_or_create(
                                    from_word=word,
                                    to_word=target_word,
                                    defaults={'status': 'pending', 'order': 1}
                                )
                                
                                if not created:
                                    updated_count += 1
                
                if created_count > 0 and updated_count > 0:
                    messages.success(request, f'Создано {created_count} новых слов и обновлено {updated_count} переводов')
                elif created_count > 0:
                    messages.success(request, f'Создано {created_count} новых переводов')
                elif updated_count > 0:
                    messages.success(request, f'Обновлено {updated_count} переводов')
                else:
                    messages.info(request, 'Переводы уже существуют')
                
                return redirect('dictionary:word_translations_dashboard')
                
            except Exception as e:
                messages.error(request, f'Ошибка при сохранении переводов: {str(e)}')
    
    # Получить слова для перевода с улучшенными фильтрами
    source_language = request.GET.get('source_lang', '')
    category_id = request.GET.get('category', '')
    search_query = request.GET.get('search', '')
    limit = int(request.GET.get('limit', 20))
    
    words = Word.objects.filter(is_deleted=False)
    
    if source_language:
        words = words.filter(language__code=source_language)
    
    if category_id:
        words = words.filter(category_id=category_id)
    
    if search_query:
        words = words.filter(word__icontains=search_query)
    
    # Исключаем слова, которые уже имеют переводы на все языки
    words = words.annotate(
        translation_count=Count('from_translations', filter=Q(from_translations__status='approved'))
    )
    
    words = words.order_by('word')[:limit]
    
    # Получить данные для фильтров
    languages = Language.objects.all().order_by('code')
    categories = Category.objects.all().order_by('code')
    
    # Статистика
    total_words = Word.objects.filter(is_deleted=False).count()
    words_with_translations = Word.objects.filter(
        is_deleted=False,
        from_translations__status='approved'
    ).distinct().count()
    
    context = {
        'words': words,
        'languages': languages,
        'categories': categories,
        'source_language': source_language,
        'category_id': category_id,
        'search_query': search_query,
        'limit': str(limit),
        'total_words': total_words,
        'words_with_translations': words_with_translations,
        'translation_progress': round((words_with_translations / total_words * 100) if total_words > 0 else 0, 1)
    }
    return render(request, 'dictionary/bulk_multi_translate.html', context)

@staff_member_required
def auto_fill_translations(request):
    """API для автозаполнения переводов на основе существующих данных"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            word_ids = data.get('word_ids', [])
            target_languages = data.get('target_languages', [])
            
            auto_filled_translations = {}
            
            for word_id in word_ids:
                try:
                    word = Word.objects.get(id=word_id)
                    
                    for lang_code in target_languages:
                        # Ищем существующие переводы этого слова на целевой язык
                        existing_translations = Translation.objects.filter(
                            from_word=word,
                            to_word__language__code=lang_code,
                            status='approved'
                        ).select_related('to_word')
                        
                        if existing_translations.exists():
                            # Берем первый найденный перевод
                            translation = existing_translations.first()
                            auto_filled_translations[f"{word_id}_{lang_code}"] = translation.to_word.word
                        else:
                            # Ищем похожие слова на целевом языке
                            similar_words = Word.objects.filter(
                                language__code=lang_code,
                                word__icontains=word.word[:3],  # Поиск по первым 3 буквам
                                is_deleted=False
                            )[:1]
                            
                            if similar_words.exists():
                                auto_filled_translations[f"{word_id}_{lang_code}"] = f"[SIMILAR] {similar_words.first().word}"
                            else:
                                # Генерируем заглушку
                                auto_filled_translations[f"{word_id}_{lang_code}"] = f"[AUTO] {word.word} ({lang_code})"
                
                except Word.DoesNotExist:
                    continue
            
            return JsonResponse({
                'success': True,
                'translations': auto_filled_translations
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

@staff_member_required
def quick_translate(request):
    """Список всех терминов с фильтрацией и поиском"""
    # Получение параметров фильтрации
    search_query = request.GET.get('q', '')
    language_filter = request.GET.get('language', '')
    category_filter = request.GET.get('category', '')
    tag_filter = request.GET.get('tag', '')
    sort_by = request.GET.get('sort', 'word')  # word, category, created_at
    sort_order = request.GET.get('order', 'asc')  # asc, desc
    
    # Базовый queryset
    words = Word.objects.filter(is_deleted=False, status='approved')
    
    # Фильтрация по поиску
    if search_query:
        words = words.filter(
            Q(word__icontains=search_query) |
            Q(meaning__icontains=search_query) |
            Q(category__code__icontains=search_query) |
            Q(tags__code__icontains=search_query)
        ).distinct()
    
    # Фильтрация по языку
    if language_filter:
        words = words.filter(language__code=language_filter)
    
    # Фильтрация по категории
    if category_filter:
        words = words.filter(category_id=category_filter)
    
    # Фильтрация по тегу
    if tag_filter:
        words = words.filter(tags__code=tag_filter)
    
    # Сортировка
    if sort_by == 'category':
        words = words.order_by('category__code', 'word')
    elif sort_by == 'created_at':
        words = words.order_by('created_at')
    else:
        words = words.order_by('word')
    
    if sort_order == 'desc':
        words = words.reverse()
    
    # Пагинация
    paginator = Paginator(words, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Получение данных для фильтров
    languages = Language.objects.all().order_by('code')
    categories = Category.objects.all().order_by('code')
    tags = Tag.objects.all().order_by('code')
    
    # Статистика
    total_terms = Word.objects.filter(is_deleted=False, status='approved').count()
    terms_with_translations = Word.objects.filter(
        is_deleted=False, 
        status='approved',
        from_translations__status='approved'
    ).distinct().count()
    
    context = {
        'page_obj': page_obj,
        'languages': languages,
        'categories': categories,
        'tags': tags,
        'search_query': search_query,
        'language_filter': language_filter,
        'category_filter': category_filter,
        'tag_filter': tag_filter,
        'sort_by': sort_by,
        'sort_order': sort_order,
        'total_terms': total_terms,
        'terms_with_translations': terms_with_translations,
        'translation_progress': round((terms_with_translations / total_terms * 100) if total_terms > 0 else 0, 1)
    }
    
    return render(request, 'dictionary/quick_translate.html', context)

@staff_member_required
def quick_translate_detail(request, term_id):
    """Детальная страница термина с переводами"""
    word = get_object_or_404(Word, id=term_id, is_deleted=False)
    
    if request.method == 'POST':
        # Обработка сохранения переводов
        try:
            with transaction.atomic():
                # Обновление основной информации
                if 'category' in request.POST:
                    word.category_id = request.POST['category']
                
                if 'tags' in request.POST:
                    tag_names = [tag.strip() for tag in request.POST['tags'].split(',') if tag.strip()]
                    # Создаем или получаем теги
                    tags = []
                    for tag_name in tag_names:
                        tag, created = Tag.objects.get_or_create(code=tag_name.lower())
                        tags.append(tag)
                    word.tags.set(tags)
                
                word.save()
                
                # Обработка переводов
                languages = Language.objects.exclude(id=word.language.id)
                created_count = 0
                updated_count = 0
                
                for language in languages:
                    translation_key = f'translation_{language.code}'
                    description_key = f'description_{language.code}'
                    
                    if translation_key in request.POST and request.POST[translation_key].strip():
                        translation_text = request.POST[translation_key].strip()
                        description_text = request.POST.get(description_key, '').strip()
                        
                        # Проверяем существующее слово
                        existing_word = Word.objects.filter(
                            word=translation_text,
                            language=language,
                            is_deleted=False
                        ).first()
                        
                        if existing_word:
                            target_word = existing_word
                            # Обновляем описание если оно изменилось
                            if existing_word.meaning != description_text and description_text:
                                existing_word.meaning = description_text
                                existing_word.save()
                        else:
                            # Создаем новое слово
                            target_word = Word.objects.create(
                                word=translation_text,
                                language=language,
                                meaning=description_text or word.meaning,
                                category=word.category,
                                status='pending',
                                created_by=request.user
                            )
                            created_count += 1
                        
                        # Создаем или обновляем перевод
                        translation, created = Translation.objects.get_or_create(
                            from_word=word,
                            to_word=target_word,
                            defaults={'status': 'pending', 'order': 1}
                        )
                        
                        if not created:
                            updated_count += 1
                
                if created_count > 0 or updated_count > 0:
                    messages.success(request, f'Сохранено {created_count} новых переводов и обновлено {updated_count} существующих')
                else:
                    messages.info(request, 'Изменения сохранены')
                
                return redirect('dictionary:quick_translate_detail', term_id=word.id)
                
        except Exception as e:
            messages.error(request, f'Ошибка при сохранении: {str(e)}')
    
    # Получение переводов
    translations = {}
    languages = Language.objects.exclude(id=word.language.id)
    
    for language in languages:
        # Ищем существующий перевод
        translation = Translation.objects.filter(
            from_word=word,
            to_word__language=language,
            status='approved'
        ).select_related('to_word').first()
        
        if translation:
            translations[language.code] = {
                'word': translation.to_word,
                'translation': translation,
                'exists': True
            }
        else:
            translations[language.code] = {
                'word': None,
                'translation': None,
                'exists': False
            }
    
    # Получение данных для форм
    categories = Category.objects.all().order_by('code')
    all_tags = Tag.objects.all().order_by('code')
    
    context = {
        'word': word,
        'translations': translations,
        'languages': languages,
        'categories': categories,
        'all_tags': all_tags,
        'current_tags': word.tags.all()
    }
    
    return render(request, 'dictionary/quick_translate_detail.html', context)

@staff_member_required
def word_create(request):
    """Создание нового слова"""
    if request.method == 'POST':
        form = WordForm(request.POST)
        if form.is_valid():
            word = form.save(commit=False)
            word.created_by = request.user
            word.save()
            form.save_m2m()  # Сохраняем many-to-many поля (tags)
            messages.success(request, f'Слово "{word.word}" успешно создано')
            return redirect('dictionary:word_detail', word_id=word.id)
    else:
        form = WordForm()
    
    context = {
        'form': form,
        'title': 'Создание нового слова',
        'submit_text': 'Создать слово'
    }
    return render(request, 'dictionary/word_form.html', context)

@staff_member_required
def word_edit(request, word_id):
    """Редактирование слова"""
    word = get_object_or_404(Word, id=word_id)
    
    if request.method == 'POST':
        form = WordForm(request.POST, instance=word)
        if form.is_valid():
            word = form.save()
            messages.success(request, f'Слово "{word.word}" успешно обновлено')
            return redirect('dictionary:word_detail', word_id=word.id)
    else:
        form = WordForm(instance=word)
    
    context = {
        'form': form,
        'word': word,
        'title': f'Редактирование слова "{word.word}"',
        'submit_text': 'Сохранить изменения'
    }
    return render(request, 'dictionary/word_form.html', context)

@staff_member_required
def term_list(request):
    """Список всех терминов с фильтрацией и поиском"""
    # Получение параметров фильтрации
    search_query = request.GET.get('q', '')
    language_filter = request.GET.get('language', '')
    category_filter = request.GET.get('category', '')
    tag_filter = request.GET.get('tag', '')
    sort_by = request.GET.get('sort', 'word')  # word, category, created_at
    sort_order = request.GET.get('order', 'asc')  # asc, desc
    
    # Базовый queryset
    words = Word.objects.filter(is_deleted=False, status='approved')
    
    # Фильтрация по поиску
    if search_query:
        words = words.filter(
            Q(word__icontains=search_query) |
            Q(meaning__icontains=search_query) |
            Q(category__code__icontains=search_query) |
            Q(tags__code__icontains=search_query)
        ).distinct()
    
    # Фильтрация по языку
    if language_filter:
        words = words.filter(language__code=language_filter)
    
    # Фильтрация по категории
    if category_filter:
        words = words.filter(category_id=category_filter)
    
    # Фильтрация по тегу
    if tag_filter:
        words = words.filter(tags__code=tag_filter)
    
    # Сортировка
    if sort_by == 'category':
        words = words.order_by('category__code', 'word')
    elif sort_by == 'created_at':
        words = words.order_by('created_at')
    else:
        words = words.order_by('word')
    
    if sort_order == 'desc':
        words = words.reverse()
    
    # Пагинация
    paginator = Paginator(words, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Получение данных для фильтров
    languages = Language.objects.all().order_by('code')
    categories = Category.objects.all().order_by('code')
    tags = Tag.objects.all().order_by('code')
    
    # Статистика
    total_terms = Word.objects.filter(is_deleted=False, status='approved').count()
    terms_with_translations = Word.objects.filter(
        is_deleted=False, 
        status='approved',
        from_translations__status='approved'
    ).distinct().count()
    
    context = {
        'page_obj': page_obj,
        'languages': languages,
        'categories': categories,
        'tags': tags,
        'search_query': search_query,
        'language_filter': language_filter,
        'category_filter': category_filter,
        'tag_filter': tag_filter,
        'sort_by': sort_by,
        'sort_order': sort_order,
        'total_terms': total_terms,
        'terms_with_translations': terms_with_translations,
        'translation_progress': round((terms_with_translations / total_terms * 100) if total_terms > 0 else 0, 1)
    }
    
    return render(request, 'dictionary/term_list.html', context)

@staff_member_required
def term_detail(request, term_id):
    """Детальная страница термина с переводами"""
    word = get_object_or_404(Word, id=term_id, is_deleted=False)
    
    if request.method == 'POST':
        # Обработка сохранения переводов
        try:
            with transaction.atomic():
                # Обновление основной информации
                if 'category' in request.POST:
                    word.category_id = request.POST['category']
                
                if 'tags' in request.POST:
                    tag_names = [tag.strip() for tag in request.POST['tags'].split(',') if tag.strip()]
                    # Создаем или получаем теги
                    tags = []
                    for tag_name in tag_names:
                        tag, created = Tag.objects.get_or_create(code=tag_name.lower())
                        tags.append(tag)
                    word.tags.set(tags)
                
                word.save()
                
                # Обработка переводов
                languages = Language.objects.exclude(id=word.language.id)
                created_count = 0
                updated_count = 0
                
                for language in languages:
                    translation_key = f'translation_{language.code}'
                    description_key = f'description_{language.code}'
                    
                    if translation_key in request.POST and request.POST[translation_key].strip():
                        translation_text = request.POST[translation_key].strip()
                        description_text = request.POST.get(description_key, '').strip()
                        
                        # Проверяем существующее слово
                        existing_word = Word.objects.filter(
                            word=translation_text,
                            language=language,
                            is_deleted=False
                        ).first()
                        
                        if existing_word:
                            target_word = existing_word
                            # Обновляем описание если оно изменилось
                            if existing_word.meaning != description_text and description_text:
                                existing_word.meaning = description_text
                                existing_word.save()
                        else:
                            # Создаем новое слово
                            target_word = Word.objects.create(
                                word=translation_text,
                                language=language,
                                meaning=description_text or word.meaning,
                                category=word.category,
                                status='pending',
                                created_by=request.user
                            )
                            created_count += 1
                        
                        # Создаем или обновляем перевод
                        translation, created = Translation.objects.get_or_create(
                            from_word=word,
                            to_word=target_word,
                            defaults={'status': 'pending', 'order': 1}
                        )
                        
                        if not created:
                            updated_count += 1
                
                if created_count > 0 or updated_count > 0:
                    messages.success(request, f'Сохранено {created_count} новых переводов и обновлено {updated_count} существующих')
                else:
                    messages.info(request, 'Изменения сохранены')
                
                return redirect('dictionary:term_detail', term_id=word.id)
                
        except Exception as e:
            messages.error(request, f'Ошибка при сохранении: {str(e)}')
    
    # Получение переводов
    translations = {}
    languages = Language.objects.exclude(id=word.language.id)
    
    for language in languages:
        # Ищем существующий перевод
        translation = Translation.objects.filter(
            from_word=word,
            to_word__language=language,
            status='approved'
        ).select_related('to_word').first()
        
        if translation:
            translations[language.code] = {
                'word': translation.to_word,
                'translation': translation,
                'exists': True
            }
        else:
            translations[language.code] = {
                'word': None,
                'translation': None,
                'exists': False
            }
    
    # Получение данных для форм
    categories = Category.objects.all().order_by('code')
    all_tags = Tag.objects.all().order_by('code')
    
    context = {
        'word': word,
        'translations': translations,
        'languages': languages,
        'categories': categories,
        'all_tags': all_tags,
        'current_tags': word.tags.all()
    }
    
    return render(request, 'dictionary/term_detail.html', context)
