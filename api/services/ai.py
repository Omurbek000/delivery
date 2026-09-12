"""AI-помощник: цепочка OpenCode -> Gemini -> Groq -> fallback + кэш + FAQ."""

import json
import logging
import re

import requests
from django.conf import settings
from django.core.cache import cache

from api.models import Dish

logger = logging.getLogger('api')

# FAQ — частые вопросы (кэшируются на 1 час как и обычные запросы)
FAQ_KEYWORDS = {
    'вкусные': ['посоветуй вкусные', 'какие вкусные', 'самые вкусные', 'что вкусное', 'топ роллы', 'топ блюд'],
    'популярные': ['популярные', 'хиты', 'что берут', 'что заказывают', 'бестселлер'],
    'дешевые': ['дешевые', 'недорогие', 'дешево', 'бюджет', 'подешевле'],
    'дорогие': ['дорогие', 'премиум', 'люкс'],
    'доставка': ['доставляете', 'доставка', 'сколько ждать', 'время доставки'],
}

# Ключевые слова для fallback
CHEESE_WORDS = ['сыр', 'cheese', 'сливочный', 'филадельфия', 'моцарелла']
MEAT_WORDS = ['куриц', 'говяд', 'свинин', 'лосось', 'тунец', 'краб', 'угорь', 'кревет', 'мясо', 'рыб']
SPICY_WORDS = ['спайси', 'остр', 'чили', 'wasabi', 'васаби']


def _get_menu() -> list[dict]:
    """Возвращает меню для промпта — только доступные блюда."""
    dishes = Dish.objects.filter(is_available=True).select_related('category')
    menu = []
    for d in dishes:
        menu.append({
            'id': d.id,
            'name': d.name,
            'description': d.description or '',
            'ingredients': getattr(d, 'ingredients', '') or '',
            'price': str(d.price),
            'category': d.category.name if d.category else '',
        })
    return menu


def _fallback_recommend(query: str) -> dict:
    """Rule-based fallback — работает без ключей."""
    query_low = query.lower()
    menu = _get_menu()
    candidates = []

    if 'без сыра' in query_low:
        for item in menu:
            text = f"{item['name']} {item['description']} {item['ingredients']}".lower()
            if not any(w in text for w in CHEESE_WORDS):
                if 'ролл' in query_low and 'ролл' not in item['category'].lower() and 'ролл' not in item['name'].lower():
                    continue
                if 'суши' in query_low and 'суши' not in item['category'].lower():
                    continue
                candidates.append(item)
        if candidates:
            candidates = sorted(candidates, key=lambda x: (0 if 'ролл' in x['name'].lower() or 'суши' in x['name'].lower() else 1, x['name']))
            return {
                'answer': f"Нашел {len(candidates)} блюд без сыра — смотри подборку.",
                'dish_ids': [c['id'] for c in candidates[:8]],
                'dishes': candidates[:8],
                'source': 'fallback',
            }

    if any(p in query_low for p in ['нас трое', 'на троих', 'на 3', '3 человека', 'три человека', 'на троих', 'сет', 'компани']):
        food = [m for m in menu if m['category'] in ('Суши', 'Роллы')]
        if not food:
            food = menu
        sorted_menu = sorted(food, key=lambda x: float(x['price']), reverse=True)
        picked = sorted_menu[:3]
        total = sum(float(p['price']) for p in picked)
        return {
            'answer': f'На троих берите 3 ролла по 8 шт (24 кусочка) — {", ".join(p["name"] for p in picked)} на {total:.0f} сом. Хватит всем.',
            'dish_ids': [c['id'] for c in picked],
            'dishes': picked,
            'source': 'fallback',
        }

    if 'пицц' in query_low:
        pizza_alt = [m for m in menu if 'хот' in m['name'].lower() or 'запеч' in m['ingredients'].lower()]
        if pizza_alt:
            candidates = pizza_alt[:3]
        else:
            candidates = menu[:3]
        return {
            'answer': 'Пиццы у нас нет, но попробуй запеченный Хот-ролл — похож на пиццу, с сыром и лососем. Или бери сет из 3 роллов.',
            'dish_ids': [c['id'] for c in candidates],
            'dishes': candidates,
            'source': 'fallback',
        }

    if any(w in query_low for w in ['остр', 'спайси']):
        for item in menu:
            text = f"{item['name']} {item['description']} {item['ingredients']}".lower()
            if any(w in text for w in SPICY_WORDS):
                candidates.append(item)
        if candidates:
            return {
                'answer': f"Острое — {len(candidates)} позиций.",
                'dish_ids': [c['id'] for c in candidates[:8]],
                'dishes': candidates[:8],
                'source': 'fallback',
            }

    if 'вегет' in query_low:
        for item in menu:
            text = f"{item['name']} {item['description']} {item['ingredients']}".lower()
            if not any(w in text for w in MEAT_WORDS):
                candidates.append(item)
        if candidates:
            return {
                'answer': f"Вегетарианское — {len(candidates)} блюд.",
                'dish_ids': [c['id'] for c in candidates[:8]],
                'dishes': candidates[:8],
                'source': 'fallback',
            }

    # FAQ: "какие вкусные" — отдаем хиты (самые дорогие как популярные)
    if any(p in query_low for p in FAQ_KEYWORDS['вкусные'] + FAQ_KEYWORDS['популярные']):
        sorted_menu = sorted(menu, key=lambda x: float(x['price']), reverse=True)
        picked = sorted_menu[:3]
        return {
            'answer': 'Самые вкусные и популярные — бери эти 3 хита, их чаще всего заказывают.',
            'dish_ids': [c['id'] for c in picked],
            'dishes': picked,
            'source': 'fallback',
        }

    if any(p in query_low for p in FAQ_KEYWORDS['дешевые']):
        sorted_menu = sorted(menu, key=lambda x: float(x['price']))
        picked = sorted_menu[:3]
        return {
            'answer': 'Бюджетно — вот 3 самых недорогих.',
            'dish_ids': [c['id'] for c in picked],
            'dishes': picked,
            'source': 'fallback',
        }

    if any(p in query_low for p in FAQ_KEYWORDS['дорогие']):
        sorted_menu = sorted(menu, key=lambda x: float(x['price']), reverse=True)
        picked = sorted_menu[:3]
        return {
            'answer': 'Премиум — топ-3 дорогих.',
            'dish_ids': [c['id'] for c in picked],
            'dishes': picked,
            'source': 'fallback',
        }

    if any(p in query_low for p in FAQ_KEYWORDS['доставка']):
        picked = sorted(menu, key=lambda x: float(x['price']), reverse=True)[:2]
        return {
            'answer': 'Доставляем по Бишкеку 30-45 мин. Готовим 15 мин + дорога. Бери что-то из хитов пока ждешь.',
            'dish_ids': [c['id'] for c in picked],
            'dishes': picked,
            'source': 'fallback',
        }

    words = re.findall(r'\w+', query_low)
    for item in menu:
        text = f"{item['name']} {item['description']} {item['ingredients']} {item['category']}".lower()
        if any(w in text for w in words if len(w) > 2):
            candidates.append(item)
    if candidates:
        return {
            'answer': f"Подобрал {len(candidates)} блюд по запросу.",
            'dish_ids': [c['id'] for c in candidates[:8]],
            'dishes': candidates[:8],
            'source': 'fallback',
        }

    return {
        'answer': 'Точно такого нет, попробуй эти популярные блюда.',
        'dish_ids': [c['id'] for c in menu[:3]],
        'dishes': menu[:3],
        'source': 'fallback',
    }


def _call_openai_compatible(query: str, menu: list[dict], base_url: str, api_key: str, model: str, source_name: str) -> dict | None:
    """Универсальный вызов OpenAI-совместимого API (OpenCode, Groq, OpenAI, OpenRouter)."""
    if not api_key or not base_url:
        return None
    system = (
        'Ты — помощник ресторана «Онигири». Отвечай только по меню, не выдумывай блюда. '
        'Если просят "без сыра" — исключай блюда где в составе есть сыр, сливочный сыр, филадельфия. '
        'Если "нас трое" — советуй сет или 2-3 ролла. '
        'Верни СТРОГО JSON вида {"answer": "текст", "dish_ids": [1,2]} без markdown.'
    )
    menu_text = json.dumps(menu, ensure_ascii=False)
    prompt = f'{system}\nМеню: {menu_text}\nЗапрос: {query}\nВерни JSON.'

    url = base_url.rstrip('/') + '/chat/completions'
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    payload = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.4,
        'max_tokens': 800,
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=12)
        resp.raise_for_status()
        data = resp.json()
        text = data['choices'][0]['message']['content']
        text = re.sub(r'^```(?:json)?', '', text.strip())
        text = re.sub(r'```$', '', text.strip())
        m = re.search(r'\{.*\}', text, re.S)
        if m:
            parsed = json.loads(m.group())
            valid_ids = {m['id'] for m in menu}
            dish_ids = [i for i in parsed.get('dish_ids', []) if i in valid_ids][:8]
            return {
                'answer': parsed.get('answer', 'Вот подборка.'),
                'dish_ids': dish_ids,
                'source': source_name,
            }
    except Exception as e:
        logger.warning(f'{source_name} error: {e}')
    return None


def _call_gemini(query: str, menu: list[dict]) -> dict | None:
    """Gemini Flash."""
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not api_key:
        return None
    model = getattr(settings, 'GEMINI_MODEL', 'gemini-1.5-flash')
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}'
    system = (
        'Ты — помощник ресторана «Онигири». Отвечай только по меню, не выдумывай блюда. '
        'Если просят "без сыра" — исключай блюда где в составе есть сыр, сливочный сыр, филадельфия. '
        'Если "нас трое" — советуй сет или 2-3 ролла. '
        'Верни СТРОГО JSON вида {"answer": "текст", "dish_ids": [1,2]} без markdown.'
    )
    menu_text = json.dumps(menu, ensure_ascii=False)
    prompt = f'{system}\nМеню: {menu_text}\nЗапрос: {query}\nВерни JSON.'
    payload = {
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {'temperature': 0.4, 'maxOutputTokens': 800},
    }
    try:
        resp = requests.post(url, json=payload, timeout=12)
        resp.raise_for_status()
        data = resp.json()
        text = data['candidates'][0]['content']['parts'][0]['text']
        text = re.sub(r'^```(?:json)?', '', text.strip())
        text = re.sub(r'```$', '', text.strip())
        m = re.search(r'\{.*\}', text, re.S)
        if m:
            parsed = json.loads(m.group())
            valid_ids = {m['id'] for m in menu}
            dish_ids = [i for i in parsed.get('dish_ids', []) if i in valid_ids][:8]
            return {
                'answer': parsed.get('answer', 'Вот подборка.'),
                'dish_ids': dish_ids,
                'source': 'gemini',
            }
    except Exception as e:
        logger.warning(f'Gemini error: {e}')
    return None


def _call_opencode(query: str, menu: list[dict]) -> dict | None:
    """OpenCode — пробует все модели из OPENCODE_MODELS по одному ключу."""
    api_key = getattr(settings, 'OPENCODE_API_KEY', '')
    base_url = getattr(settings, 'OPENCODE_BASE_URL', '')
    models = getattr(settings, 'OPENCODE_MODELS', None) or [getattr(settings, 'OPENCODE_MODEL', 'opencode/muse-spark-1.2-contributor-free')]
    if not api_key or not base_url or not models:
        return None
    for model in models:
        result = _call_openai_compatible(query, menu, base_url=base_url, api_key=api_key, model=model, source_name=f'opencode:{model}')
        if result is not None:
            # Приводим source к opencode для фронта
            result['source'] = 'opencode'
            return result
        logger.info(f"OpenCode model {model} failed, next")
    return None


def _call_groq(query: str, menu: list[dict]) -> dict | None:
    """Groq llama."""
    return _call_openai_compatible(
        query, menu,
        base_url=getattr(settings, 'GROQ_BASE_URL', 'https://api.groq.com/openai/v1'),
        api_key=getattr(settings, 'GROQ_API_KEY', ''),
        model=getattr(settings, 'GROQ_MODEL', 'llama-3.1-8b-instant'),
        source_name='groq',
    )


def recommend(query: str) -> dict:
    """Цепочка: opencode → gemini → groq → fallback + кэш на 1 час."""
    import hashlib
    query = (query or '').strip()
    if not query:
        menu = _get_menu()[:5]
        return {
            'answer': 'Напиши что хочешь: "без сыра", "на троих", "острое".',
            'dish_ids': [m['id'] for m in menu],
            'dishes': menu,
            'source': 'fallback',
        }
    menu = _get_menu()
    if not menu:
        return {'answer': 'Меню пустое.', 'dish_ids': [], 'dishes': [], 'source': 'fallback'}

    # Кэш: хешируем чтобы не было проблем с кириллицей в memcached
    raw_key = query.lower().strip()
    cache_key = "ai:" + hashlib.md5(raw_key.encode('utf-8')).hexdigest()
    cached = cache.get(cache_key)
    if cached:
        logger.info(f"AI cache hit for '{query}'")
        return cached

    order = getattr(settings, 'AI_PROVIDER_ORDER', ['opencode', 'gemini', 'groq', 'fallback'])
    callers = {
        'opencode': _call_opencode,
        'gemini': _call_gemini,
        'groq': _call_groq,
    }

    result = None
    for provider in order:
        if provider == 'fallback':
            result = _fallback_recommend(query)
            break
        func = callers.get(provider)
        if not func:
            continue
        result = func(query, menu)
        if result is not None:
            # Если LLM вернул пустые dish_ids — считаем неудачей, идем дальше
            if not result.get('dish_ids'):
                logger.info(f"AI {provider} empty dish_ids, switching to next")
                continue
            if 'dishes' not in result or not result['dishes']:
                id_map = {m['id']: m for m in menu}
                result['dishes'] = [id_map[i] for i in result.get('dish_ids', []) if i in id_map]
            logger.info(f"AI {provider} success for query '{query}'")
            break
        logger.info(f"AI {provider} failed, switching to next")

    if result is None or not result.get('dish_ids'):
        result = _fallback_recommend(query)

    # Кэшируем на 1 час (и LLM и fallback — не важно, одинаковые запросы частые)
    try:
        cache.set(cache_key, result, timeout=getattr(settings, 'AI_CACHE_TIMEOUT', 3600))
    except Exception:
        pass
    return result
