"""
Представления (views) приложения vacancies — поиск вакансий.

  - VacancySearchView — поиск: обращается к API HeadHunter, а при его
                        недоступности ищет по вакансиям в своей базе
  - VacancyListView   — список всех сохранённых вакансий
  - VacancyDetailView — одна вакансия по её id
"""

import requests
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
# Q позволяет строить условия с ИЛИ: Q(name=...) | Q(description=...)
from django.db.models import Q
from django.utils import timezone
from .models import Vacancy, SearchQuery
from .serializers import VacancySerializer, SearchQuerySerializer
from core.services.hh_service import HeadHunterService


class VacancySearchView(APIView):
    """
    Поиск вакансий.  POST /api/vacancies/search/

    Алгоритм работы:
      1. Проверить данные запроса (должность обязательна)
      2. Сохранить запрос в историю поиска
      3. Перевести название города в числовой код региона HH
      4. Запросить вакансии у API HeadHunter
      5. Если API недоступен — искать по локальной базе (демо-режим)
      6. Сохранить найденные вакансии в свою базу и вернуть фронтенду
    """

    def post(self, request):
        # Весь метод обёрнут в try/except: при любой неожиданной ошибке
        # вернётся понятный JSON, а не HTML-страница ошибки Django
        try:
            # print-ы оставлены намеренно: это журнал работы поиска,
            # по нему видно, какие параметры реально ушли в HH API
            print("=== SEARCH REQUEST ===")
            print("Request data:", request.data)

            # Сериализатор проверяет входные данные: должность не короче
            # 2 символов, зарплата — число и т.д.
            serializer = SearchQuerySerializer(data=request.data)
            if not serializer.is_valid():
                print("Serializer errors:", serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # validated_data — уже проверенные и приведённые к нужным типам данные
            validated_data = serializer.validated_data
            print("Validated data:", validated_data)

            # Сохраняем запрос
            # ** распаковывает словарь в аргументы: position=..., city=...
            SearchQuery.objects.create(
                user=request.user,
                **validated_data
            )

            hh_service = HeadHunterService()

            # Карта городов -> коды регионов HH API (проверены через api.hh.ru/areas)
            # HH принимает в параметре area только числовой код региона,
            # название города он не понимает
            CITY_MAP = {
                # Казахстан
                'Астана': 159,
                'Нур-Султан': 159,
                'Алматы': 160,
                'Шымкент': 205,
                'Караганда': 177,
                'Актобе': 154,
                'Тараз': 187,
                'Павлодар': 181,
                'Усть-Каменогорск': 194,
                'Семей': 185,
                'Костанай': 172,
                'Петропавловск': 180,
                'Уральск': 193,
                'Атырау': 153,
                'Актау': 152,
                'Кызылорда': 174,
                # Россия
                'Москва': 1,
                'Санкт-Петербург': 2,
                'Новосибирск': 4,
                'Екатеринбург': 3,
                'Казань': 88,
                'Нижний Новгород': 66,
                'Краснодар': 53,
                'Ростов-на-Дону': 76,
                'Самара': 78,
                'Уфа': 99,
                'Красноярск': 54,
                'Воронеж': 26,
                'Пермь': 72,
                'Волгоград': 24,
            }

            # Параметры запроса к HH API:
            # text — поисковая строка, per_page — сколько вакансий вернуть за раз
            params = {
                'text': validated_data['position'],
                'per_page': 50,
            }

            # Обработка города
            city = validated_data.get('city')
            # strip() убирает случайные пробелы, введённые пользователем
            city_name = city.strip() if city else ''
            # Флаг: удалось ли отфильтровать по городу средствами HH API.
            # Нужен ниже, чтобы не фильтровать результаты повторно
            city_resolved_by_area = False
            if city_name:
                print(f"Searching in city: {city_name}")

                # Пробуем найти код города (точное совпадение, затем без учета регистра)
                # next(генератор, None) вернёт первое совпадение или None,
                # если такого города в справочнике нет
                city_code = CITY_MAP.get(city_name) or next(
                    (code for name, code in CITY_MAP.items() if name.lower() == city_name.lower()),
                    None
                )
                if city_code:
                    # Нашли код — HH сам отфильтрует вакансии по региону (точный способ)
                    params['area'] = city_code
                    city_resolved_by_area = True
                    print(f"Using HH area code: {city_code} for city: {city_name}")
                else:
                    # Если город не найден в карте, пробуем поиск по тексту
                    # (неточный способ: название города ищется в тексте вакансии)
                    params['text'] = f"{params['text']} {city_name}"
                    print(f"City not in map, adding to text search: {city_name}")

            # Обработка зарплаты
            # HH трактует этот параметр как "зарплата не ниже указанной"
            salary_desired = validated_data.get('salary_desired')
            if salary_desired:
                params['salary'] = salary_desired
                print(f"Salary filter: {salary_desired}")

            # Добавляем языки программирования
            # У HH нет отдельного фильтра по технологиям, поэтому
            # выбранные языки просто дописываются в поисковую строку
            programming_languages = validated_data.get('programming_languages', [])
            if programming_languages:
                params['text'] = f"{params['text']} {' '.join(programming_languages)}"
                print(f"Programming languages: {programming_languages}")

            print("Final HH API params:", params)

            # Выполняем поиск
            response = hh_service.search_vacancies(params)

            if not response:
                print("HH API returned empty response")
                return Response(
                    {'error': 'Сервис HH.ru временно недоступен'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # HH API недоступен (с апреля 2026 публичный поиск вакансий на HH
            # требует токен работодателя и отдаёт 403 анонимным запросам) —
            # ищем по вакансиям, сохранённым в локальной базе.
            if response.get('error'):
                print(f"HH API unavailable ({response['error']}), falling back to local search")
                local_results = self._search_local_vacancies(
                    validated_data['position'],
                    city_name,
                    validated_data.get('salary_desired'),
                    validated_data.get('programming_languages', []),
                )
                print(f"Local search found {len(local_results)} vacancies")

                if local_results:
                    return Response(VacancySerializer(local_results, many=True).data)

                return Response(
                    {
                        'message': f'По запросу "{validated_data["position"]}" в городе '
                                   f'"{city_name or "любой"}" вакансий не найдено',
                        'suggestions': [
                            'Попробуйте изменить запрос',
                            'Уберите фильтр по городу',
                            'Используйте более общие ключевые слова',
                        ],
                    },
                    status=status.HTTP_200_OK
                )

            # Структура ответа не та, что ожидалась (формат API изменился)
            if 'items' not in response:
                print("HH API response without 'items':", response)
                return Response(
                    {'error': 'Не удалось получить данные от HH.ru'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            print(f"HH API found {len(response.get('items', []))} items")

            # Сохраняем найденные вакансии
            vacancies_data = []
            items = response.get('items', [])[:20]  # Ограничиваем 20 вакансиями

            for item in items:
                # try внутри цикла: если одна вакансия пришла с битыми данными,
                # обработка остальных не прерывается
                try:
                    # Переводим ответ HH в формат полей нашей модели
                    vacancy_data = hh_service.parse_vacancy_data(item)

                    # Доп. проверка города только если не использовался area-код
                    # (HH API уже отфильтровал по area, повторная текстовая проверка
                    # только отсеивала бы верные результаты из-за разных написаний,
                    # например "Нур-Султан (Астана)" vs "Астана")
                    vacancy_city = vacancy_data.get('city', '')
                    if city_name and not city_resolved_by_area and vacancy_city:
                        if city_name.lower() not in vacancy_city.lower():
                            print(f"Skipping vacancy from {vacancy_city} (not {city_name})")
                            continue

                    # Сохраняем в базу
                    # update_or_create: вакансия с таким hh_id уже есть —
                    # обновляем её данные, нет — создаём. Так не появляются дубли
                    vacancy, created = Vacancy.objects.update_or_create(
                        hh_id=vacancy_data['hh_id'],
                        defaults=vacancy_data
                    )
                    
                    vacancies_data.append(VacancySerializer(vacancy).data)
                    
                except Exception as e:
                    print(f"Error processing vacancy item: {str(e)}")
                    continue

            print(f"Processed {len(vacancies_data)} vacancies")

            if not vacancies_data:
                return Response(
                    {
                        'message': f'По запросу "{validated_data["position"]}" в городе "{city if city else "любой"}" вакансий не найдено',
                        'suggestions': [
                            'Попробуйте изменить запрос',
                            'Уберите фильтр по городу',
                            'Используйте более общие ключевые слова'
                        ]
                    },
                    status=status.HTTP_200_OK
                )

            return Response(vacancies_data)
            
        except Exception as e:
            print(f"Error in VacancySearchView: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Внутренняя ошибка сервера: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _search_local_vacancies(self, position, city_name, salary_desired, programming_languages):
        """Поиск по вакансиям в локальной базе."""
        # Начинаем со всех вакансий и последовательно сужаем выборку.
        # Запрос в БД при этом не выполняется — Django собирает его «лениво»
        # и обращается к базе только в конце, когда результат реально нужен
        queryset = Vacancy.objects.all()

        # Любое из слов запроса в названии, описании или требованиях
        # Запрос разбивается на слова: "Frontend разработчик" -> ["Frontend", "разработчик"].
        # Отсекаем односимвольные слова (предлоги), они дают мусорные совпадения
        tokens = [t for t in (position or '').split() if len(t) > 1]
        if tokens:
            # Q() — пустое условие, к нему через | (ИЛИ) добавляем проверки
            position_filter = Q()
            for token in tokens:
                # icontains = "содержит подстроку, без учёта регистра"
                position_filter |= (
                    Q(name__icontains=token)
                    | Q(description__icontains=token)
                    | Q(requirements__icontains=token)
                )
            queryset = queryset.filter(position_filter)

        # Фильтр по городу
        if city_name:
            queryset = queryset.filter(city__icontains=city_name)

        # Фильтр по зарплате: gte = "больше или равно" (greater than or equal)
        if salary_desired:
            queryset = queryset.filter(salary_from__gte=salary_desired)

        # Фильтр по языкам: достаточно совпадения хотя бы с одним выбранным
        if programming_languages:
            lang_filter = Q()
            for lang in programming_languages:
                lang_filter |= (
                    Q(name__icontains=lang)
                    | Q(description__icontains=lang)
                    | Q(requirements__icontains=lang)
                )
            queryset = queryset.filter(lang_filter)

        # Сортируем по дате публикации и ограничиваем 50 вакансиями.
        # list() выполняет запрос к базе и превращает результат в список
        return list(queryset.order_by('-published_at')[:50])


class VacancyListView(generics.ListAPIView):
    """
    Список всех вакансий из базы.  GET /api/vacancies/

    ListAPIView — готовый класс DRF: сам обрабатывает GET-запрос,
    поэтому достаточно указать, что отдавать (queryset) и чем
    преобразовывать в JSON (serializer_class).
    Используется фронтендом при открытии страницы вакансий.
    """

    serializer_class = VacancySerializer
    queryset = Vacancy.objects.all().order_by('-published_at')


class VacancyDetailView(generics.RetrieveAPIView):
    """
    Одна вакансия по её id.  GET /api/vacancies/<id>/

    RetrieveAPIView сам находит объект по id из адреса
    и возвращает 404, если такой вакансии нет.
    """

    serializer_class = VacancySerializer
    queryset = Vacancy.objects.all()