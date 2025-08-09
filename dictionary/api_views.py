# API views для редактирования категорий и тегов
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from .models import Category, CategoryTranslation, Tag, TagTranslation, Word
import json


@staff_member_required
def get_category_api(request, category_id):
    """API для получения данных категории"""
    try:
        category = Category.objects.get(id=category_id)
        try:
            translation = category.translations.get(language__code='ru')
            name = translation.name
        except CategoryTranslation.DoesNotExist:
            translation = category.translations.first()
            name = translation.name if translation else category.code
        
        return JsonResponse({
            'success': True,
            'category': {'id': category.id, 'code': category.code, 'name': name}
        })
    except Category.DoesNotExist:
        return JsonResponse({'error': 'Категория не найдена'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
def update_category_api(request, category_id):
    """API для обновления категории"""
    if request.method != 'PUT':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)
    
    try:
        category = Category.objects.get(id=category_id)
        data = json.loads(request.body)
        code = data.get('code', '').strip()
        name = data.get('name', '').strip()
        
        if not code or not name:
            return JsonResponse({'error': 'Код и название обязательны'}, status=400)
        
        if Category.objects.filter(code=code).exclude(id=category_id).exists():
            return JsonResponse({'error': f'Категория с кодом "{code}" уже существует'}, status=400)
        
        category.code = code
        category.save()
        
        for translation in category.translations.all():
            translation.name = name
            translation.save()
        
        return JsonResponse({
            'success': True,
            'category': {'id': category.id, 'code': category.code, 'name': name}
        })
        
    except Category.DoesNotExist:
        return JsonResponse({'error': 'Категория не найдена'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Некорректный JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required  
def delete_category_api(request, category_id):
    """API для удаления категории"""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)
    
    try:
        category = Category.objects.get(id=category_id)
        words_count = Word.objects.filter(category=category).count()
        if words_count > 0:
            return JsonResponse({
                'error': f'Нельзя удалить категорию, используемую в {words_count} словах'
            }, status=400)
        
        category.delete()
        return JsonResponse({'success': True})
        
    except Category.DoesNotExist:
        return JsonResponse({'error': 'Категория не найдена'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
def get_tags_api(request):
    """API для получения списка тегов"""
    try:
        tags = []
        for tag in Tag.objects.all().order_by('code'):
            try:
                translation = tag.translations.get(language__code='ru')
                name = translation.name
            except TagTranslation.DoesNotExist:
                translation = tag.translations.first()
                name = translation.name if translation else tag.code
            
            tags.append({'id': tag.id, 'code': tag.code, 'name': name})
        
        return JsonResponse({'success': True, 'tags': tags})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
def update_tag_api(request, tag_id):
    """API для обновления тега"""
    if request.method != 'PUT':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)
    
    try:
        tag = Tag.objects.get(id=tag_id)
        data = json.loads(request.body)
        code = data.get('code', '').strip()
        name = data.get('name', '').strip()
        
        if not code or not name:
            return JsonResponse({'error': 'Код и название обязательны'}, status=400)
        
        if Tag.objects.filter(code=code).exclude(id=tag_id).exists():
            return JsonResponse({'error': f'Тег с кодом "{code}" уже существует'}, status=400)
        
        tag.code = code
        tag.save()
        
        for translation in tag.translations.all():
            translation.name = name
            translation.save()
        
        return JsonResponse({
            'success': True,
            'tag': {'id': tag.id, 'code': tag.code, 'name': name}
        })
        
    except Tag.DoesNotExist:
        return JsonResponse({'error': 'Тег не найден'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Некорректный JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
def delete_tag_api(request, tag_id):
    """API для удаления тега"""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)
    
    try:
        tag = Tag.objects.get(id=tag_id)
        words_count = Word.objects.filter(tags=tag).count()
        if words_count > 0:
            return JsonResponse({
                'error': f'Нельзя удалить тег, используемый в {words_count} словах'
            }, status=400)
        
        tag.delete()
        return JsonResponse({'success': True})
        
    except Tag.DoesNotExist:
        return JsonResponse({'error': 'Тег не найден'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
