import random
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dictionary_django.settings')
django.setup()

from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from dictionary.models import Language, Category, CategoryTranslation, Tag, TagTranslation, Word, Translation

# Sample legal terms (75 per language, expandable)
LEGAL_TERMS = {
    'ru': [
        ('преступление', 'Нарушение закона, влекущее уголовную ответственность', '/prʲɪstʊˈplʲenʲɪje/'),
        ('договор', 'Соглашение между сторонами', '/dɐɡɐˈvor/'),
        ('суд', 'Орган правосудия', '/sud/'),
        ('адвокат', 'Лицо, представляющее интересы в суде', '/ɐdvoˈkat/'),
        ('закон', 'Нормативный правовой акт', '/zaˈkon/'),
        ('право', 'Совокупность норм и правил', '/praˈvo/'),
        ('ответственность', 'Обязанность отвечать за свои действия', '/ɐtvʲɪtstvʲɪnˈnostʲ/'),
        ('наказание', 'Мера государственного принуждения', '/nɐkɐˈzanʲɪje/'),
        ('иск', 'Требование в суд', '/isk/'),
        ('приговор', 'Решение суда по уголовному делу', '/prʲɪɡɐˈvor/'),
        # Add more terms (up to 75)
    ] + [(f'закон_{i}', f'Закон номер {i}', f'/zaˈkon_{i}/') for i in range(11, 76)],  # Placeholder terms
    'kk': [
        ('қылмыс', 'Заңды бұзу', '/qɯlmɯs/'),
        ('шарт', 'Тараптар арасындағы келісім', '/ʃart/'),
        ('сот', 'Әділет органы', '/sot/'),
        ('адвокат', 'Сотта мүдделерді қорғаушы', '/advokat/'),
        ('заң', 'Нормативті құқықтық акт', '/zaŋ/'),
        ('құқық', 'Нормалар мен ережелер жиынтығы', '/qɯqɯq/'),
        ('жауапкершілік', 'Өз әрекеттері үшін жауап беру міндеті', '/ʒawapkerʃilik/'),
        ('жаза', 'Мемлекеттік мәжбүрлеу шарасы', '/ʒaza/'),
        ('талап', 'Сотқа талап', '/talap/'),
        ('үкім', 'Қылмыстық іс бойынша сот шешімі', '/ykim/'),
        # Add more terms
    ] + [(f'заң_{i}', f'Заң нөмірі {i}', f'/zaŋ_{i}/') for i in range(11, 76)],
    'en': [
        ('crime', 'An act violating the law', '/kraɪm/'),
        ('contract', 'An agreement between parties', '/ˈkɒntrækt/'),
        ('court', 'A judicial body', '/kɔːrt/'),
        ('lawyer', 'A person representing legal interests', '/ˈlɔɪər/'),
        ('law', 'A normative legal act', '/lɔː/'),
        ('right', 'A set of norms and rules', '/raɪt/'),
        ('responsibility', 'Obligation to answer for actions', '/rɪˌspɒnsɪˈbɪlɪti/'),
        ('punishment', 'A measure of state coercion', '/ˈpʌnɪʃmənt/'),
        ('claim', 'A demand to court', '/kleɪm/'),
        ('sentence', 'Court decision in criminal case', '/ˈsentəns/'),
        # Add more terms
    ] + [(f'law_{i}', f'Law number {i}', f'/lɔː_{i}/') for i in range(11, 76)],
    'tr': [
        ('suç', 'Yasayı ihlal eden bir eylem', '/sutʃ/'),
        ('sözleşme', 'Taraflar arasındaki anlaşma', '/søzleʃme/'),
        ('mahkeme', 'Adalet organı', '/mahˈkeme/'),
        ('avukat', 'Mahkemede çıkarları temsil eden kişi', '/avuˈkat/'),
        ('kanun', 'Normatif hukuki akt', '/kaˈnun/'),
        ('hak', 'Normlar ve kurallar topluluğu', '/hak/'),
        ('sorumluluk', 'Eylemlerden dolayı cevap verme yükümlülüğü', '/sorumluˈluk/'),
        ('ceza', 'Devlet zorlaması önlemi', '/dʒeˈza/'),
        ('dava', 'Mahkemeye talep', '/daˈva/'),
        ('hüküm', 'Ceza davasında mahkeme kararı', '/hyˈkym/'),
        # Add more terms
    ] + [(f'kanun_{i}', f'Kanun numarası {i}', f'/kanun_{i}/') for i in range(11, 76)],
}

# Define languages, categories, and tags
LANGUAGES = [
    {'code': 'ru', 'name': 'Русский'},
    {'code': 'kk', 'name': 'Қазақша'},
    {'code': 'en', 'name': 'English'},
    {'code': 'tr', 'name': 'Türkçe'},
]

CATEGORIES = [
    {
        'code': 'criminal_law',
        'translations': {
            'ru': {'name': 'Уголовное право', 'description': 'Термины уголовного законодательства'},
            'kk': {'name': 'Қылмыстық құқық', 'description': 'Қылмыстық заңнама терминдері'},
            'en': {'name': 'Criminal Law', 'description': 'Terms of criminal legislation'},
            'tr': {'name': 'Ceza Hukuku', 'description': 'Ceza mevzuatı terimleri'},
        }
    },
    {
        'code': 'civil_law',
        'translations': {
            'ru': {'name': 'Гражданское право', 'description': 'Термины гражданского законодательства'},
            'kk': {'name': 'Азаматтық құқық', 'description': 'Азаматтық заңнама терминдері'},
            'en': {'name': 'Civil Law', 'description': 'Terms of civil legislation'},
            'tr': {'name': 'Medeni Hukuk', 'description': 'Medeni mevzuat terimleri'},
        }
    },
    {
        'code': 'court_procedure',
        'translations': {
            'ru': {'name': 'Судебный процесс', 'description': 'Термины судебных процедур'},
            'kk': {'name': 'Сот процесі', 'description': 'Сот процедураларының терминдері'},
            'en': {'name': 'Court Procedure', 'description': 'Terms of court procedures'},
            'tr': {'name': 'Mahkeme Usulü', 'description': 'Mahkeme prosedürleri terimleri'},
        }
    },
]

TAGS = [
    {
        'code': 'noun',
        'translations': {
            'ru': 'существительное',
            'kk': 'зат есім',
            'en': 'noun',
            'tr': 'isim',
        }
    },
    {
        'code': 'legal_term',
        'translations': {
            'ru': 'юридический термин',
            'kk': 'құқықтық термин',
            'en': 'legal term',
            'tr': 'hukuki terim',
        }
    },
]

@transaction.atomic
def populate_legal_terms():
    print("Starting population of legal terms...")
    
    # Get or create default user
    User = get_user_model()
    try:
        default_user = User.objects.get(username='admin')
    except User.DoesNotExist:
        default_user = User.objects.create_user(username='admin', password='admin123', email='admin@example.com')
        print("Created default user: admin")

    # Create languages
    language_objects = {}
    for lang in LANGUAGES:
        lang_obj, created = Language.objects.get_or_create(code=lang['code'], defaults={'name': lang['name']})
        language_objects[lang['code']] = lang_obj
        if created:
            print(f"Created language: {lang['name']} ({lang['code']})")

    # Create categories and their translations
    category_objects = {}
    for cat in CATEGORIES:
        cat_obj, created = Category.objects.get_or_create(code=cat['code'])
        category_objects[cat['code']] = cat_obj
        if created:
            print(f"Created category: {cat['code']}")
        
        for lang_code, trans in cat['translations'].items():
            cat_trans, created = CategoryTranslation.objects.get_or_create(
                category=cat_obj,
                language=language_objects[lang_code],
                defaults={'name': trans['name'], 'description': trans['description']}
            )
            if created:
                print(f"Created category translation: {cat['code']} -> {lang_code}")

    # Create tags and their translations
    tag_objects = {}
    for tag in TAGS:
        tag_obj, created = Tag.objects.get_or_create(code=tag['code'])
        tag_objects[tag['code']] = tag_obj
        if created:
            print(f"Created tag: {tag['code']}")
        
        for lang_code, trans in tag['translations'].items():
            tag_trans, created = TagTranslation.objects.get_or_create(
                tag=tag_obj,
                language=language_objects[lang_code],
                defaults={'name': trans}
            )
            if created:
                print(f"Created tag translation: {tag['code']} -> {lang_code}")

    # Create words
    word_objects = {lang: [] for lang in language_objects}
    for lang_code, terms in LEGAL_TERMS.items():
        print(f"Creating words for language: {lang_code}")
        for word_text, meaning, pronunciation in terms:
            word, created = Word.objects.get_or_create(
                word=word_text,
                language=language_objects[lang_code],
                defaults={
                    'meaning': meaning,
                    'pronunciation': pronunciation,
                    'category': random.choice(list(category_objects.values())),
                    'status': 'approved',
                    'difficulty': 'medium',
                    'created_by': default_user,
                }
            )
            if created:
                print(f"Created word: {word_text} ({lang_code})")
            
            # Assign random tags
            available_tags = list(tag_objects.values())
            if available_tags:
                num_tags = random.randint(1, min(2, len(available_tags)))
                selected_tags = random.sample(available_tags, num_tags)
                word.tags.set(selected_tags)
            
            word_objects[lang_code].append(word)

    # Create translations (link words across languages)
    print("Creating translations between languages...")
    for i in range(len(LEGAL_TERMS['ru'])):
        for from_lang in ['ru', 'kk', 'en']:
            for to_lang in ['kk', 'en', 'tr']:
                if from_lang != to_lang and i < len(word_objects[from_lang]) and i < len(word_objects[to_lang]):
                    translation, created = Translation.objects.get_or_create(
                        from_word=word_objects[from_lang][i],
                        to_word=word_objects[to_lang][i],
                        defaults={'status': 'approved', 'order': 0}
                    )
                    if created:
                        print(f"Created translation: {word_objects[from_lang][i].word} -> {word_objects[to_lang][i].word}")

    print("Population complete!")
    print(f"Created {sum(len(words) for words in word_objects.values())} words")
    print(f"Created {Translation.objects.count()} translations")

if __name__ == '__main__':
    populate_legal_terms() 