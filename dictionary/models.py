from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import translation
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.db.models import Q


class TimestampedModel(models.Model):
    """Абстрактная модель с временными метками"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class SluggedModel(models.Model):
    """Абстрактная модель с автоматическим slug"""
    slug = models.SlugField(max_length=100, unique=True, blank=True, help_text='URL-friendly идентификатор')
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.get_slug_source())
        super().save(*args, **kwargs)
    
    def get_slug_source(self):
        """Переопределить в дочерних классах"""
        return str(self)
    
    class Meta:
        abstract = True


class Language(models.Model):
    """Справочник поддерживаемых языков."""
    code = models.CharField(max_length=10, unique=True)  # 'ru', 'kk', 'en', 'tr'
    name = models.CharField(max_length=50)  # 'Русский', 'Қазақша', 'English', 'Türkçe'
    
    @property
    def word_count(self):
        """Количество слов на этом языке"""
        return self.word_set.filter(is_deleted=False, status='approved').count()
    
    def get_translation_progress(self):
        """Процент переведенных категорий и тегов на этот язык"""
        from django.db.models import Count
        total_categories = Category.objects.count()
        total_tags = Tag.objects.count()
        
        translated_categories = self.categorytranslation_set.count()
        translated_tags = self.tagtranslation_set.count()
        
        total_items = total_categories + total_tags
        translated_items = translated_categories + translated_tags
        
        return round((translated_items / total_items * 100) if total_items > 0 else 0, 1)
    
    def __str__(self):
        return f'{self.name} ({self.code})'
    
    class Meta:
        ordering = ['code']
        verbose_name = 'Язык'
        verbose_name_plural = 'Языки'

class CustomUser(AbstractUser):
    preferred_language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True, related_name='users', help_text='Язык интерфейса по умолчанию')
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_moderator = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    registration_source = models.CharField(max_length=50, blank=True, help_text='Источник регистрации (email, google, ... )')
    def activate_language(self):
        if self.preferred_language:
            translation.activate(self.preferred_language.code)
    def __str__(self):
        return self.username

class Category(SluggedModel, TimestampedModel):
    code = models.CharField(max_length=50, unique=True)  # например, 'animals', 'food'
    
    def get_slug_source(self):
        return self.code
    
    def get_name(self, language_code='ru'):
        """Получить название на определенном языке"""
        try:
            return self.translations.get(language__code=language_code).name
        except CategoryTranslation.DoesNotExist:
            return self.code
    
    @property
    def word_count(self):
        """Количество слов в этой категории"""
        return self.words.filter(is_deleted=False, status='approved').count()
    
    def __str__(self):
        return self.code
    
    def get_absolute_url(self):
        return f'/category/{self.slug}/'
    
    class Meta:
        ordering = ['code']
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

class CategoryTranslation(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='translations')
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    class Meta:
        unique_together = ('category', 'language')
    def __str__(self):
        return f'{self.category.code} [{self.language.code}]: {self.name[:20]}...'

class Tag(SluggedModel, TimestampedModel):
    DISPLAY_CHOICES = [
        ('visible', 'Показывать'),
        ('hidden', 'Скрыть'),
    ]
    
    code = models.CharField(max_length=30, unique=True)  # например, 'noun', 'verb'
    display_mode = models.CharField(max_length=10, choices=DISPLAY_CHOICES, default='visible', help_text='Режим отображения тега')
    
    def get_slug_source(self):
        return self.code
    
    def get_name(self, language_code='ru'):
        """Получить название на определенном языке"""
        try:
            return self.translations.get(language__code=language_code).name
        except TagTranslation.DoesNotExist:
            return self.code
    
    @property
    def word_count(self):
        """Количество слов с этим тегом"""
        return self.words.filter(is_deleted=False, status='approved').count()
    
    def __str__(self):
        return self.code
    
    def get_absolute_url(self):
        return f'/tag/{self.slug}/'
    
    class Meta:
        ordering = ['code']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

class TagTranslation(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='translations')
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    class Meta:
        unique_together = ('tag', 'language')
    def __str__(self):
        return f'{self.tag.code} [{self.language.code}]: {self.name[:20]}...'


class WordQuerySet(models.QuerySet):
    """Кастомный QuerySet для модели Word"""
    
    def published(self):
        """Только опубликованные и не удаленные слова"""
        return self.filter(status='approved', is_deleted=False)
    
    def by_language(self, language_code):
        """Фильтр по языку"""
        return self.filter(language__code=language_code)
    
    def by_difficulty(self, difficulty):
        """Фильтр по уровню сложности"""
        return self.filter(difficulty=difficulty)
    
    def with_translations(self):
        """Слова у которых есть переводы"""
        return self.filter(from_translations__isnull=False).distinct()
    
    def without_translations(self):
        """Слова без переводов"""
        return self.filter(from_translations__isnull=True)
    
    def by_category(self, category_code):
        """Фильтр по категории"""
        return self.filter(category__code=category_code)
    
    def recent(self, days=30):
        """Недавно добавленные слова"""
        from django.utils import timezone
        from datetime import timedelta
        date_threshold = timezone.now() - timedelta(days=days)
        return self.filter(created_at__gte=date_threshold)


class WordManager(models.Manager):
    """Кастомный менеджер для модели Word"""
    
    def get_queryset(self):
        return WordQuerySet(self.model, using=self._db)
    
    def published(self):
        return self.get_queryset().published()
    
    def by_language(self, language_code):
        return self.get_queryset().by_language(language_code)
    
    def by_difficulty(self, difficulty):
        return self.get_queryset().by_difficulty(difficulty)
    
    def with_translations(self):
        return self.get_queryset().with_translations()
    
    def without_translations(self):
        return self.get_queryset().without_translations()
    
    def recent(self, days=30):
        return self.get_queryset().recent(days=days)


class Word(models.Model):
    """Слово на определённом языке."""
    STATUS_CHOICES = [
        ('pending', 'На проверке'),
        ('approved', 'Опубликовано'),
        ('rejected', 'Отклонено'),
    ]
    DIFFICULTY_LEVELS = [
        ('none', 'Без уровня'),
        ('hidden', 'Не показывать'),
        ('easy', 'Легко'),
        ('medium', 'Средне'),
        ('hard', 'Сложно'),
    ]
    word = models.CharField(max_length=100)
    slug = models.SlugField(max_length=150, unique=True, blank=True, help_text='URL-friendly идентификатор')
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    meaning = models.TextField()
    # Если нужно поддерживать несколько категорий для одного слова, раскомментируйте:
    # categories = models.ManyToManyField(Category, blank=True, related_name='words')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='words')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    tags = models.ManyToManyField(Tag, blank=True, related_name='words')
    image = models.ImageField(upload_to='word_images/', blank=True, null=True)
    file = models.FileField(upload_to='word_files/', blank=True, null=True)
    pronunciation = models.CharField(max_length=100, blank=True, help_text='МФА, транскрипция и т.д.')
    audio = models.FileField(upload_to='word_audio/', blank=True, null=True, help_text='Аудио слова')
    example_audio = models.FileField(upload_to='example_audio/', blank=True, null=True, help_text='Аудио примера')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_LEVELS, default='none', blank=True, null=True)
    is_deleted = models.BooleanField(default=False, help_text='Soft-delete: не удалять из БД, а скрывать')
    created_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='added_words')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    translations = models.ManyToManyField('self', through='Translation', symmetrical=False, related_name='reverse_translations')
    
    # Кастомный менеджер
    objects = WordManager()
    
    @property
    def is_published(self):
        """Проверка что слово опубликовано"""
        return self.status == 'approved' and not self.is_deleted
    
    @property 
    def translation_count(self):
        """Количество переводов этого слова"""
        return self.from_translations.filter(status='approved').count()
    
    def get_translations_for_language(self, language_code):
        """Получить переводы на определенный язык"""
        return self.from_translations.filter(
            to_word__language__code=language_code,
            status='approved'
        ).select_related('to_word', 'to_word__language')
    
    def get_first_translation(self, language_code):
        """Получить первый перевод на язык"""
        translations = self.get_translations_for_language(language_code)
        return translations.first().to_word if translations.exists() else None
    
    def has_audio(self):
        """Проверка наличия аудиофайлов"""
        return bool(self.audio or self.example_audio)
    
    def get_tags_display(self):
        """Получить теги в виде строки"""
        return ', '.join([tag.code for tag in self.tags.all()])
    
    class Meta:
        unique_together = ('word', 'language')
        ordering = ['word']
        verbose_name = 'Слово'
        verbose_name_plural = 'Слова'
        indexes = [
            models.Index(fields=['word']),
            models.Index(fields=['language']),
            models.Index(fields=['status']),
            models.Index(fields=['slug']),
            models.Index(fields=['created_at']),
            models.Index(fields=['difficulty']),
        ]
    
    def generate_unique_slug(self):
        """Генерирует уникальный slug для слова"""
        if not self.word:
            return None
            
        base_slug = slugify(self.word)
        if not base_slug:
            base_slug = f"word-{self.pk or 'new'}"
        
        lang_suffix = f"-{self.language.code}"
        slug = base_slug + lang_suffix
        
        # Проверяем уникальность
        counter = 1
        original_slug = slug
        max_attempts = 100
        
        while Word.objects.filter(slug=slug).exclude(pk=self.pk).exists() and counter <= max_attempts:
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        # Если не удалось найти уникальный slug
        if counter > max_attempts:
            import time
            timestamp = int(time.time())
            slug = f"{original_slug}-{timestamp}"
            
            if Word.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                import random
                random_suffix = random.randint(1000, 9999)
                slug = f"{original_slug}-{timestamp}-{random_suffix}"
        
        # Проверяем длину
        if len(slug) > 150:
            lang_suffix = f"-{self.language.code}"
            max_base_length = 150 - len(lang_suffix)
            base_slug = slug[:-len(lang_suffix)]
            if max_base_length > 0:
                slug = base_slug[:max_base_length] + lang_suffix
            else:
                slug = f"word-{self.pk or 'new'}{lang_suffix}"
        
        return slug
    
    def clean(self):
        """Валидация модели перед сохранением"""
        super().clean()
        
        # Проверяем, что слово не пустое
        if not self.word or not self.word.strip():
            raise ValidationError('Название слова не может быть пустым')
        
        # Проверяем, что значение не пустое
        if not self.meaning or not self.meaning.strip():
            raise ValidationError('Значение слова не может быть пустым')
        
        # Проверяем уникальность слова на том же языке
        if self.pk:  # Для существующего слова
            existing = Word.objects.filter(
                word=self.word, 
                language=self.language
            ).exclude(pk=self.pk).first()
        else:  # Для нового слова
            existing = Word.objects.filter(
                word=self.word, 
                language=self.language
            ).first()
        
        if existing:
            raise ValidationError(
                f'Слово "{self.word}" на языке {self.language.name} уже существует'
            )
    
    def save(self, *args, **kwargs):
        if not self.slug:
            # Создаем slug из слова и языка
            base_slug = slugify(self.word)
            if not base_slug:  # Если slugify вернул пустую строку
                base_slug = f"word-{self.pk or 'new'}"
            
            lang_suffix = f"-{self.language.code}"
            self.slug = base_slug + lang_suffix
            
            # Проверяем уникальность slug и добавляем счетчик если нужно
            counter = 1
            original_slug = self.slug
            max_attempts = 100  # Защита от бесконечного цикла
            
            while Word.objects.filter(slug=self.slug).exclude(pk=self.pk).exists() and counter <= max_attempts:
                self.slug = f"{original_slug}-{counter}"
                counter += 1
            
            # Если не удалось найти уникальный slug после max_attempts попыток
            if counter > max_attempts:
                # Генерируем slug с timestamp
                import time
                timestamp = int(time.time())
                self.slug = f"{original_slug}-{timestamp}"
                
                # Проверяем, что и этот slug уникален
                if Word.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                    # Последняя попытка - добавляем случайное число
                    import random
                    random_suffix = random.randint(1000, 9999)
                    self.slug = f"{original_slug}-{timestamp}-{random_suffix}"
        
        # Дополнительная проверка длины slug
        if len(self.slug) > 150:  # max_length для slug поля
            # Обрезаем slug до максимальной длины, сохраняя суффикс языка
            lang_suffix = f"-{self.language.code}"
            max_base_length = 150 - len(lang_suffix)
            base_slug = self.slug[:-len(lang_suffix)]
            if max_base_length > 0:
                self.slug = base_slug[:max_base_length] + lang_suffix
            else:
                # Если даже с суффиксом языка slug слишком длинный
                self.slug = f"word-{self.pk or 'new'}{lang_suffix}"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f'{self.word} ({self.language.code})'
    
    def get_absolute_url(self):
        return f'/word/{self.slug}/'

class Translation(models.Model):
    """Связь между словами на разных языках (перевод).
    Если нужна симметрия (A→B = B→A), реализуйте через signals или вручную."""
    from_word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='from_translations')
    to_word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='to_translations')
    note = models.CharField(max_length=100, blank=True, help_text='Дополнительные примечания к переводу')
    order = models.PositiveIntegerField(default=0, help_text='Порядок отображения переводов')
    status = models.CharField(max_length=10, choices=Word.STATUS_CHOICES, default='approved', help_text='Статус перевода')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def clean(self):
        """Валидация перевода"""
        if hasattr(self, 'from_word') and hasattr(self, 'to_word'):
            if self.from_word.language == self.to_word.language:
                raise ValidationError('Нельзя переводить слово на тот же язык')
            
            if self.from_word == self.to_word:
                raise ValidationError('Слово не может быть переводом самого себя')
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f'{self.from_word.word} → {self.to_word.word}'
    
    class Meta:
        unique_together = ('from_word', 'to_word')
        ordering = ['from_word', 'order']
        verbose_name = 'Перевод'
        verbose_name_plural = 'Переводы'

class Example(TimestampedModel):
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='examples')
    text = models.TextField(help_text='Пример использования слова')
    author = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_examples')
    
    def __str__(self):
        return f'Пример для "{self.word.word}": {self.text[:50]}...'
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Пример'
        verbose_name_plural = 'Примеры'

class Favourite(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='favourites')
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='favourited_by')
    added_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.user.username} → {self.word.word}'
    
    class Meta:
        unique_together = ('user', 'word')
        ordering = ['-added_at']
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

class SearchHistory(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='search_history')
    word = models.CharField(max_length=100)
    searched_at = models.DateTimeField(auto_now_add=True)

class WordLike(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='word_likes')
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='likes')
    is_like = models.BooleanField(help_text='True для лайка, False для дизлайка')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        action = '👍' if self.is_like else '👎'
        return f'{self.user.username} {action} {self.word.word}'
    
    class Meta:
        unique_together = ('user', 'word')
        ordering = ['-created_at']
        verbose_name = 'Оценка слова'
        verbose_name_plural = 'Оценки слов'

class WordChangeLog(models.Model):
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='change_logs')
    user = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20)  # 'created', 'updated', 'deleted', 'status_changed'
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True)
    change_type = models.CharField(max_length=20, blank=True, help_text='manual, auto, import и т.д.')

class WordHistory(models.Model):
    """Версионирование слов (для отката и аудита)."""
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='history')
    data = models.JSONField()
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True)

class InterfaceTranslation(models.Model):
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    key = models.CharField(max_length=100)      # Например: 'menu.home', 'button.save'
    value = models.TextField()                  # Переведённый текст
    class Meta:
        unique_together = ('language', 'key')
    def __str__(self):
        v = self.value if len(self.value) <= 20 else self.value[:17] + '...'
        return f'{self.language.code}: {self.key} = {v}'

        