import requests
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.utils import timezone
from .models import Vacancy, SearchQuery
from .serializers import VacancySerializer, SearchQuerySerializer
from core.services.hh_service import HeadHunterService


class VacancySearchView(APIView):
    def post(self, request):
        try:
            print("=== SEARCH REQUEST ===")
            print("Request data:", request.data)
            
            serializer = SearchQuerySerializer(data=request.data)
            if not serializer.is_valid():
                print("Serializer errors:", serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            validated_data = serializer.validated_data
            print("Validated data:", validated_data)
            
            # Сохраняем запрос
            SearchQuery.objects.create(
                user=request.user,
                **validated_data
            )

            hh_service = HeadHunterService()

            # Карта городов для HH API (коды областей Казахстана)
            CITY_MAP = {
                'Астана': 159,  # Нур-Султан (Астана)
                'Алматы': 160,  # Алматы
                'Шымкент': 213,  # Шымкент
                'Караганда': 167,  # Карагандинская область
                'Актобе': 162,  # Актюбинская область
                'Тараз': 168,  # Жамбылская область
                'Павлодар': 165,  # Павлодарская область
                'Усть-Каменогорск': 163,  # Восточно-Казахстанская область
                'Семей': 163,  # Восточно-Казахстанская область
                'Костанай': 164,  # Костанайская область
                'Петропавловск': 166,  # Северо-Казахстанская область
                'Уральск': 169,  # Западно-Казахстанская область
                'Атырау': 161,  # Атырауская область
                'Актау': 170,  # Мангистауская область
                'Кызылорда': 172,  # Кызылординская область
            }

            params = {
                'text': validated_data['position'],
                'per_page': 50,
            }

            # Обработка города
            city = validated_data.get('city')
            if city and city.strip():
                city_name = city.strip()
                print(f"Searching in city: {city_name}")
                
                # Пробуем найти код города
                city_code = CITY_MAP.get(city_name)
                if city_code:
                    params['area'] = city_code
                    print(f"Using HH area code: {city_code} for city: {city_name}")
                else:
                    # Если город не найден в карте, пробуем поиск по тексту
                    params['text'] = f"{params['text']} {city_name}"
                    print(f"City not in map, adding to text search: {city_name}")

            # Обработка зарплаты
            salary_desired = validated_data.get('salary_desired')
            if salary_desired:
                params['salary'] = salary_desired
                print(f"Salary filter: {salary_desired}")

            # Добавляем языки программирования
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
                try:
                    vacancy_data = hh_service.parse_vacancy_data(item)
                    
                    # Проверяем город вакансии
                    vacancy_city = vacancy_data.get('city', '')
                    if city and city.strip() and vacancy_city:
                        # Если указан город в фильтре, проверяем совпадение
                        if city_name.lower() not in vacancy_city.lower():
                            print(f"Skipping vacancy from {vacancy_city} (not {city_name})")
                            continue
                    
                    # Сохраняем в базу
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


class VacancyListView(generics.ListAPIView):
    serializer_class = VacancySerializer
    queryset = Vacancy.objects.all().order_by('-published_at')


class VacancyDetailView(generics.RetrieveAPIView):
    serializer_class = VacancySerializer
    queryset = Vacancy.objects.all()