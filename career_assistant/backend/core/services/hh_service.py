# backend/core/services/hh_service.py
import requests
from django.conf import settings
from datetime import datetime


class HeadHunterService:
    BASE_URL = settings.HH_API_URL
    
    def search_vacancies(self, params):
        """Поиск вакансий на HeadHunter с фильтрацией None и текстовых городов"""
        params = {k: v for k, v in params.items() if v}

        CITY_MAP = {'Москва': 113, 'Санкт-Петербург': 2}
        if 'area' in params and isinstance(params['area'], str):
            params['area'] = CITY_MAP.get(params['area'], params['area'])

        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return {'items': [], 'found': 0, 'pages': 0}

    
    def get_vacancy_details(self, vacancy_id):
        """Получение деталей вакансии"""
        try:
            response = requests.get(f"{self.BASE_URL}/{vacancy_id}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None
    
    def parse_vacancy_data(self, hh_data):
        """Парсинг данных вакансии из HH API"""
        salary = hh_data.get('salary')
        
        return {
            'hh_id': hh_data['id'],
            'name': hh_data['name'],
            'company': hh_data['employer']['name'],
            'city': hh_data['area']['name'],
            'salary_from': salary.get('from') if salary else None,
            'salary_to': salary.get('to') if salary else None,
            'salary_currency': salary.get('currency') if salary else None,
            'description': hh_data.get('description', ''),
            'requirements': hh_data.get('snippet', {}).get('requirement', ''),
            'experience': hh_data.get('experience', {}).get('name'),
            'employment_type': hh_data.get('employment', {}).get('name'),
            'schedule': hh_data.get('schedule', {}).get('name'),
            'skills': [skill['name'] for skill in hh_data.get('key_skills', [])],
            'url': hh_data.get('alternate_url'),
            'published_at': datetime.strptime(hh_data['published_at'], '%Y-%m-%dT%H:%M:%S%z')
        }