"""
Сервис интеграции с API сайта HeadHunter (hh.ru / hh.kz).

Ответственность модуля — общение с внешним API и перевод его ответа
в формат, понятный нашим моделям. Вся бизнес-логика поиска
(города, фильтры, сохранение в базу) находится в vacancies/views.py.

Архитектурно это «слой сервисов»: views не работают с requests напрямую,
а вызывают методы этого класса. Благодаря этому источник вакансий
можно заменить, не переписывая views.
"""

# backend/core/services/hh_service.py
import requests
from django.conf import settings
from datetime import datetime


class HeadHunterService:
    """Клиент API HeadHunter: поиск вакансий и разбор ответа."""

    # Адрес API берётся из настроек, а не прописан в коде —
    # чтобы менять его без правки программы (settings.HH_API_URL)
    BASE_URL = settings.HH_API_URL

    def search_vacancies(self, params):
        """Поиск вакансий на HeadHunter. Ожидает уже готовые параметры
        (area — числовой код региона HH, резолвится в vacancies.views)."""
        # Убираем пустые параметры: если отправить area='' или salary=None,
        # HH вернёт ошибку либо проигнорирует весь запрос
        params = {k: v for k, v in params.items() if v not in (None, '', [])}

        try:
            # timeout=10 обязателен: без него зависший сервер HH
            # заморозил бы наш запрос на неопределённое время
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            # Превращает коды 4xx/5xx в исключение, иначе ошибку легко пропустить
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"HH API request failed: {e}")
            # Отдельно помечаем случай, когда HH.ru вернул ошибку (403/5xx/таймаут),
            # чтобы отличать это от легитимного "по вашему запросу ничего не найдено"
            return {'items': [], 'found': 0, 'pages': 0, 'error': str(e)}

    def get_vacancy_details(self, vacancy_id):
        """Получение деталей вакансии"""
        # Список вакансий приходит в сокращённом виде; полное описание
        # доступно только по отдельному запросу к /vacancies/{id}
        try:
            response = requests.get(f"{self.BASE_URL}/{vacancy_id}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            # None = деталей нет; вызывающий код сам решает, что делать
            return None

    def parse_vacancy_data(self, hh_data):
        """Парсинг данных вакансии из HH API"""
        # Преобразуем «сырой» ответ HH в словарь с теми же именами полей,
        # что и у модели Vacancy, — его можно сразу передать в create/update

        # Зарплата может вообще отсутствовать (salary = null),
        # поэтому сначала достаём её, а ниже всюду проверяем на None
        salary = hh_data.get('salary')

        return {
            'hh_id': hh_data['id'],
            'name': hh_data['name'],
            # Вложенные объекты: employer и area — словари внутри ответа
            'company': hh_data['employer']['name'],
            'city': hh_data['area']['name'],
            # Тернарные выражения защищают от ошибки, если зарплата не указана
            'salary_from': salary.get('from') if salary else None,
            'salary_to': salary.get('to') if salary else None,
            'salary_currency': salary.get('currency') if salary else None,
            # .get() с значением по умолчанию — часть полей необязательна у HH
            'description': hh_data.get('description', ''),
            # snippet — краткая выжимка требований в результатах поиска
            'requirements': hh_data.get('snippet', {}).get('requirement', ''),
            'experience': hh_data.get('experience', {}).get('name'),
            'employment_type': hh_data.get('employment', {}).get('name'),
            'schedule': hh_data.get('schedule', {}).get('name'),
            # Навыки приходят списком словарей [{"name": "Python"}] —
            # превращаем в простой список строк ["Python"]
            'skills': [skill['name'] for skill in hh_data.get('key_skills', [])],
            'url': hh_data.get('alternate_url'),
            # Дата приходит строкой "2026-11-01T10:00:00+0300" —
            # переводим в объект datetime, который понимает Django
            'published_at': datetime.strptime(hh_data['published_at'], '%Y-%m-%dT%H:%M:%S%z')
        }
