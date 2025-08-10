from django.core.management.base import BaseCommand
from django.db import transaction
from dictionary.models import Word
from django.utils.text import slugify
import time
import random


class Command(BaseCommand):
    help = 'Исправляет дублирующиеся slug\'ы в модели Word'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет исправлено без внесения изменений',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Подробный вывод',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        self.stdout.write(
            self.style.SUCCESS('Начинаю проверку дублирующихся slug\'ов...')
        )
        
        # Находим все дублирующиеся slug'ы
        duplicate_slugs = {}
        all_words = Word.objects.all().order_by('slug', 'created_at')
        
        for word in all_words:
            if word.slug in duplicate_slugs:
                duplicate_slugs[word.slug].append(word)
            else:
                duplicate_slugs[word.slug] = [word]
        
        # Фильтруем только те slug'ы, которые действительно дублируются
        duplicate_slugs = {slug: words for slug, words in duplicate_slugs.items() if len(words) > 1}
        
        if not duplicate_slugs:
            self.stdout.write(
                self.style.SUCCESS('Дублирующихся slug\'ов не найдено!')
            )
            return
        
        self.stdout.write(
            self.style.WARNING(f'Найдено {len(duplicate_slugs)} дублирующихся slug\'ов:')
        )
        
        total_fixed = 0
        
        for slug, words in duplicate_slugs.items():
            if verbose:
                self.stdout.write(f'\nSlug: {slug}')
                for word in words:
                    self.stdout.write(f'  - {word.word} (ID: {word.pk}, язык: {word.language.code})')
            
            # Оставляем первый slug без изменений, остальные исправляем
            words_to_fix = words[1:]
            
            for word in words_to_fix:
                new_slug = self.generate_unique_slug(word)
                
                if verbose:
                    self.stdout.write(f'  Исправляю {word.word}: {slug} → {new_slug}')
                
                if not dry_run:
                    try:
                        with transaction.atomic():
                            word.slug = new_slug
                            word.save()
                            total_fixed += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Ошибка при исправлении {word.word}: {e}')
                        )
                else:
                    total_fixed += 1
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'DRY RUN: Будет исправлено {total_fixed} slug\'ов')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Успешно исправлено {total_fixed} slug\'ов')
            )
    
    def generate_unique_slug(self, word):
        """Генерирует уникальный slug для слова"""
        if not word.word:
            return None
            
        base_slug = slugify(word.word)
        if not base_slug:
            base_slug = f"word-{word.pk or 'new'}"
        
        lang_suffix = f"-{word.language.code}"
        slug = base_slug + lang_suffix
        
        # Проверяем уникальность
        counter = 1
        original_slug = slug
        max_attempts = 100
        
        while Word.objects.filter(slug=slug).exclude(pk=word.pk).exists() and counter <= max_attempts:
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        # Если не удалось найти уникальный slug
        if counter > max_attempts:
            timestamp = int(time.time())
            slug = f"{original_slug}-{timestamp}"
            
            if Word.objects.filter(slug=slug).exclude(pk=word.pk).exists():
                random_suffix = random.randint(1000, 9999)
                slug = f"{original_slug}-{timestamp}-{random_suffix}"
        
        # Проверяем длину
        if len(slug) > 150:
            lang_suffix = f"-{word.language.code}"
            max_base_length = 150 - len(lang_suffix)
            base_slug = slug[:-len(lang_suffix)]
            if max_base_length > 0:
                slug = base_slug[:max_base_length] + lang_suffix
            else:
                slug = f"word-{word.pk or 'new'}{lang_suffix}"
        
        return slug
