from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import translation

class Language(models.Model):
    """Справочник поддерживаемых языков."""
    code = models.CharField(max_length=10, unique=True)  # 'ru', 'kk', 'en', 'tr'
    name = models.CharField(max_length=50)  # 'Русский', 'Қазақша', 'English', 'Türkçe'
    def __str__(self):
        return f'{self.name} ({self.code})'

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

class Category(models.Model):
    code = models.CharField(max_length=50, unique=True)  # например, 'animals', 'food'
    def __str__(self):
        return self.code

class CategoryTranslation(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='translations')
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    class Meta:
        unique_together = ('category', 'language')
    def __str__(self):
        return f'{self.category.code} [{self.language.code}]: {self.name[:20]}...'

class Tag(models.Model):
    code = models.CharField(max_length=30, unique=True)  # например, 'noun', 'verb'
    def __str__(self):
        return self.code

class TagTranslation(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='translations')
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    class Meta:
        unique_together = ('tag', 'language')
    def __str__(self):
        return f'{self.tag.code} [{self.language.code}]: {self.name[:20]}...'

class Word(models.Model):
    """Слово на определённом языке."""
    STATUS_CHOICES = [
        ('pending', 'На проверке'),
        ('approved', 'Опубликовано'),
        ('rejected', 'Отклонено'),
    ]
    DIFFICULTY_LEVELS = [
        ('easy', 'Легко'),
        ('medium', 'Средне'),
        ('hard', 'Сложно'),
    ]
    word = models.CharField(max_length=100)
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
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_LEVELS, default='medium')
    is_deleted = models.BooleanField(default=False, help_text='Soft-delete: не удалять из БД, а скрывать')
    created_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='added_words')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    translations = models.ManyToManyField('self', through='Translation', symmetrical=False, related_name='reverse_translations')
    class Meta:
        unique_together = ('word', 'language')
        indexes = [
            models.Index(fields=['word']),
            models.Index(fields=['language']),
            models.Index(fields=['status']),
        ]
    def __str__(self):
        w = self.word if len(self.word) <= 20 else self.word[:17] + '...'
        return f'{w} ({self.language.code})'

class Translation(models.Model):
    """Связь между словами на разных языках (перевод).
    Если нужна симметрия (A→B = B→A), реализуйте через signals или вручную."""
    from_word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='from_translations')
    to_word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='to_translations')
    note = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=Word.STATUS_CHOICES, default='approved')  # статус перевода
    class Meta:
        unique_together = ('from_word', 'to_word')
    def __str__(self):
        fw = self.from_word.word if len(self.from_word.word) <= 15 else self.from_word.word[:12] + '...'
        tw = self.to_word.word if len(self.to_word.word) <= 15 else self.to_word.word[:12] + '...'
        return f'{fw} → {tw}'

class Example(models.Model):
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='examples')
    text = models.TextField()
    author = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Favourite(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='favourites')
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='favourited_by')
    added_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user', 'word')

class SearchHistory(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='search_history')
    word = models.CharField(max_length=100)
    searched_at = models.DateTimeField(auto_now_add=True)

class WordLike(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='likes')
    is_like = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user', 'word')

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

        