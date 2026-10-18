import json
import google.generativeai as genai
from django.conf import settings
import os


class GeminiService:
    def __init__(self):
        # Получаем API ключ из настроек Django
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        
        if not api_key:
            # Пробуем получить из переменных окружения как запасной вариант
            api_key = os.environ.get('GEMINI_API_KEY')
            
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY не настроен. "
                "Добавьте в settings.py: GEMINI_API_KEY = 'ваш_ключ_здесь' "
                "или установите переменную окружения GEMINI_API_KEY"
            )
        
        # Явно настраиваем с API ключом
        genai.configure(api_key=api_key)
        
        # Инициализируем модель
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def analyze_resume(self, text, job_title=None):
        # Ограничиваем длину текста для избежания переполнения токенов
        truncated_text = text[:3000] if len(text) > 3000 else text
        
        prompt = f"""
        Проанализируй резюме и дай развернутую оценку:
        
        Резюме: {truncated_text}
        
        Проанализируй по следующим критериям:
        1. Общая оценка (от 1 до 10)
        2. Сильные стороны
        3. Что нужно улучшить
        4. Что добавить
        5. Рекомендации по формату
        6. Ключевые навыки
        
        {"Для должности: " + job_title if job_title else ""}
        
        Ответ предоставь в формате JSON:
        {{
            "overall_score": float,
            "strong_points": [list of strings],
            "improvements": [list of strings],
            "additions": [list of strings],
            "format_recommendations": [list of strings],
            "key_skills": [list of strings],
            "summary": "текстовое резюме"
        }}
        
        Только JSON, без дополнительного текста.
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Извлекаем JSON из ответа
            response_text = response.text.strip()
            # Удаляем markdown коды, если есть
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            # Удаляем возможные начальные/конечные кавычки и пробелы
            response_text = response_text.strip('"\' \n')
            
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Response text: {response_text[:500]}...")  # Логируем только часть
            return self._get_default_analysis(f"Ошибка парсинга JSON: {e}")
        except Exception as e:
            print(f"Gemini API error: {e}")
            return self._get_default_analysis(str(e))
    
    def generate_cover_letter(self, resume_text, vacancy_text, style='formal'):
        styles_map = {
            'formal': 'официальный, профессиональный',
            'friendly': 'дружелюбный, теплый',
            'brief': 'краткий, по делу',
            'creative': 'креативный, нестандартный'
        }
        
        # Ограничиваем длину текстов
        truncated_resume = resume_text[:1500] if len(resume_text) > 1500 else resume_text
        truncated_vacancy = vacancy_text[:1500] if len(vacancy_text) > 1500 else vacancy_text
        
        prompt = f"""
        Сгенерируй сопроводительное письмо в {styles_map[style]} стиле.
        
        Резюме кандидата: {truncated_resume}
        
        Описание вакансии: {truncated_vacancy}
        
        Письмо должно включать:
        1. Обращение
        2. Краткое представление
        3. Соответствие требованиям вакансии
        4. Ключевые компетенции
        5. Заинтересованность в позиции
        6. Благодарность и контактная информация
        
        Длина: 200-300 слов.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error generating cover letter: {e}")
            return "Не удалось сгенерировать сопроводительное письмо. Пожалуйста, напишите его самостоятельно."
    
    def generate_interview_questions(self, resume_text, interview_type, vacancy_text=None):
        type_map = {
            'hr': 'HR интервью (общие вопросы о мотивации, опыте, карьерных целях)',
            'technical': 'Техническое интервью (вопросы по навыкам, технологиям, решению задач)',
            'stress': 'Стресс-интервью (сложные и провокационные вопросы)',
            'behavioral': 'Поведенческое интервью (ситуационные вопросы по опыту)'
        }
        
        truncated_resume = resume_text[:1500] if len(resume_text) > 1500 else resume_text
        truncated_vacancy = vacancy_text[:800] if vacancy_text and len(vacancy_text) > 800 else vacancy_text
        
        prompt = f"""
        Сгенерируй 8-10 вопросов для {type_map[interview_type]}.
        
        Резюме кандидата: {truncated_resume}
        
        {f"Описание вакансии: {truncated_vacancy}" if truncated_vacancy else ""}
        
        Предоставь вопросы в формате JSON массива:
        [
            {{"question": "текст вопроса", "category": "категория", "tips": "подсказки для ответа"}}
        ]
        
        Только JSON, без дополнительного текста.
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            # Удаляем возможные начальные/конечные кавычки
            response_text = response_text.strip('"\' \n')
            
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error for questions: {e}")
            print(f"Response text: {response_text[:500]}...")
            return []
        except Exception as e:
            print(f"Error generating questions: {e}")
            return []
    
    def _get_default_analysis(self, error_message=""):
        return {
            "overall_score": 5.0,
            "strong_points": ["Резюме требует анализа"],
            "improvements": ["Загрузите резюме для анализа"],
            "additions": ["Добавьте больше информации"],
            "format_recommendations": ["Используйте стандартный формат"],
            "key_skills": [],
            "summary": f"Требуется анализ ИИ. Ошибка: {error_message}" if error_message else "Требуется анализ ИИ"
        }
    
    def generate_test_questions(self, resume_text, category="general", difficulty="medium", count=15):
        """
        Генерирует персонализированные тестовые вопросы на основе резюме
        
        Args:
            resume_text: текст резюме
            category: категория теста
            difficulty: уровень сложности
            count: количество вопросов
            
        Returns:
            Список вопросов в формате для сохранения в БД
        """
        
        category_map = {
            'programming': 'Программирование и разработка ПО',
            'data_science': 'Наука о данных и машинное обучение',
            'design': 'Дизайн и UX/UI',
            'marketing': 'Маркетинг и продвижение',
            'management': 'Управление и менеджмент',
            'analytics': 'Аналитика и бизнес-анализ',
            'testing': 'Тестирование и QA',
            'devops': 'DevOps и инфраструктура',
            'general': 'Общие профессиональные вопросы'
        }
        
        difficulty_map = {
            'easy': 'легкий (для Junior специалистов)',
            'medium': 'средний (для Middle специалистов)', 
            'hard': 'сложный (для Senior специалистов)'
        }
        
        # Ограничиваем длину резюме
        truncated_resume = resume_text[:2000] if len(resume_text) > 2000 else resume_text
        
        prompt = f"""
        Генерируй тестовые вопросы для проверки профессиональных знаний кандидата.
        
        ИНФОРМАЦИЯ О КАНДИДАТЕ (из резюме):
        {truncated_resume}
        
        КАТЕГОРИЯ: {category_map.get(category, category)}
        УРОВЕНЬ СЛОЖНОСТИ: {difficulty_map.get(difficulty, difficulty)}
        КОЛИЧЕСТВО ВОПРОСОВ: {count}
        
        Генерируй РАЗНЫЕ ТИПЫ вопросов в пропорции:
        1. Вопросы с множественным выбором (multiple_choice) - 60%
        2. Вопросы с одиночным выбором (single_choice) - 30%
        3. Открытые вопросы (open_ended) - 10%
        
        Для КАЖДОГО вопроса укажи:
        1. question_text: Текст вопроса
        2. question_type: multiple_choice, single_choice или open_ended
        3. options: список вариантов ответа (ТОЛЬКО для multiple_choice и single_choice)
        4. correct_answer: правильный ответ (для multiple_choice - список правильных вариантов)
        5. explanation: подробное объяснение почему ответ правильный
        6. difficulty: сложность от 1 до 5
        7. skill_category: категория навыка (например: "Python", "SQL", "Алгоритмы")
        
        ТРЕБОВАНИЯ:
        1. Вопросы должны быть РЕЛЕВАНТНЫ резюме кандидата
        2. Вопросы должны проверять РЕАЛЬНЫЕ навыки, указанные в резюме
        3. Вопросы должны быть ПРАКТИЧЕСКИМИ и приближенными к реальным задачам
        4. Для сложности 'hard' добавляй вопросы по архитектуре и проектированию
        5. Для сложности 'medium' - вопросы по практическому применению
        6. Для сложности 'easy' - основы и синтаксис
        
        ФОРМАТ ОТВЕТА - строго JSON:
        {{
            "questions": [
                {{
                    "question_text": "Текст вопроса",
                    "question_type": "multiple_choice",
                    "options": ["вариант1", "вариант2", "вариант3", "вариант4"],
                    "correct_answer": ["вариант1", "вариант3"],
                    "explanation": "Подробное объяснение...",
                    "difficulty": 3,
                    "skill_category": "Python"
                }}
            ]
        }}
        
        ВАЖНО: Только JSON, без дополнительного текста и комментариев.
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Очистка ответа от markdown
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            response_text = response_text.strip('"\' \n')
            
            data = json.loads(response_text)
            
            # Преобразуем в формат для базы данных
            formatted_questions = []
            for q in data.get('questions', []):
                # Преобразуем correct_answer в строку JSON если это список
                if isinstance(q['correct_answer'], list):
                    correct_answer = json.dumps(q['correct_answer'])
                else:
                    correct_answer = str(q['correct_answer'])
                
                formatted_question = {
                    'question_text': q['question_text'],
                    'question_type': q['question_type'],
                    'options': q.get('options', []),
                    'correct_answer': correct_answer,
                    'explanation': q.get('explanation', ''),
                    'difficulty': q.get('difficulty', 3),
                    'skill_category': q.get('skill_category', 'general')
                }
                formatted_questions.append(formatted_question)
            
            return formatted_questions
            
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга JSON для тестовых вопросов: {e}")
            print(f"Ответ Gemini: {response_text[:500]}...")
            return self._get_default_test_questions(category, count)
        except Exception as e:
            print(f"Ошибка генерации тестовых вопросов: {e}")
            return self._get_default_test_questions(category, count)
    
    def _get_default_test_questions(self, category, count):
        """Вопросы по умолчанию если Gemini не сработал"""
        default_questions = []
        
        if category == 'programming':
            questions = [
                {
                    'question_text': 'Что такое переменная в программировании?',
                    'question_type': 'single_choice',
                    'options': ['Именованная область памяти', 'Функция', 'Класс', 'Метод'],
                    'correct_answer': 'Именованная область памяти',
                    'explanation': 'Переменная - это именованная область памяти, которая хранит данные.',
                    'difficulty': 1,
                    'skill_category': 'Основы программирования'
                },
                {
                    'question_text': 'Какие из этих языков являются статически типизированными?',
                    'question_type': 'multiple_choice',
                    'options': ['Java', 'Python', 'C++', 'JavaScript'],
                    'correct_answer': ['Java', 'C++'],
                    'explanation': 'Java и C++ - статически типизированные языки, Python и JavaScript - динамически типизированные.',
                    'difficulty': 2,
                    'skill_category': 'Языки программирования'
                }
            ]
        else:
            questions = [
                {
                    'question_text': 'Что такое soft skills?',
                    'question_type': 'single_choice',
                    'options': ['Навыки работы с софтом', 'Профессиональные навыки', 'Гибкие навыки', 'Технические навыки'],
                    'correct_answer': 'Гибкие навыки',
                    'explanation': 'Soft skills (гибкие навыки) - это личные качества и социальные навыки, такие как коммуникация, работа в команде, лидерство.',
                    'difficulty': 1,
                    'skill_category': 'Общее'
                }
            ]
        
        return questions[:count]
    # Добавить этот метод в класс GeminiService:

    def analyze_interview_answers(self, context):
        """
        Анализирует ответы пользователя на собеседовании
        """
        prompt = f"""
        Ты - опытный HR-специалист, который проводит анализ собеседования кандидата.
        
        КОНТЕКСТ СОБЕСЕДОВАНИЯ:
        Тип собеседования: {context['interview_type']}
        
        ВОПРОСЫ И ОТВЕТЫ:
        """
        
        # Добавляем вопросы и ответы
        for i, (question, answer) in enumerate(zip(context['questions'], context['user_answers'])):
            prompt += f"""
            Вопрос {i+1}: {question.get('question', '')}
            Категория: {question.get('category', 'Общий')}
            Ответ кандидата: {answer}
            """
        
        prompt += f"""
        
        ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ:
        {f"Информация из вакансии: {context.get('vacancy_info', '')}" if context.get('vacancy_info') else ""}
        
        ПРОАНАЛИЗИРУЙ ОТВЕТЫ КАНДИДАТА И ДАЙ РАЗВЕРНУТЫЙ ФИДБЕК:
        
        Проанализируй по следующим критериям:
        1. Общая оценка ответов (от 1 до 10)
        2. Сильные стороны ответов (что кандидат сделал хорошо)
        3. Слабые стороны ответов (что можно улучшить)
        4. Конкретные советы для улучшения
        5. Частые ошибки, которые нужно исправить
        6. Области для развития
        7. Итоговое резюме (краткий вывод)
        
        ОБРАТИ ВНИМАНИЕ НА:
        - Полноту ответов
        - Конкретность примеров
        - Уверенность в ответах
        - Соответствие требованиям типа собеседования
        - Структурированность ответов
        - Наличие конкретных метрик и результатов
        
        Предоставь ответ в формате JSON:
        {{
            "overall_score": float (от 1 до 10),
            "strengths": [list of strings],
            "weaknesses": [list of strings],
            "tips": [list of strings],
            "common_mistakes": [list of strings],
            "improvement_areas": [list of strings],
            "summary": "текстовое резюме"
        }}
        
        Только JSON, без дополнительного текста.
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Очистка ответа
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            response_text = response_text.strip('"\' \n')
            
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error for feedback: {e}")
            print(f"Response text: {response_text[:500]}...")
            return self._get_default_feedback()
        except Exception as e:
            print(f"Error analyzing interview answers: {e}")
            return self._get_default_feedback()

    def _get_default_feedback(self):
        """Возвращает дефолтный фидбек при ошибке"""
        return {
            'overall_score': 6.5,
            'strengths': [
                'Вы предоставили ответы на вопросы',
                'Показали заинтересованность в позиции'
            ],
            'weaknesses': [
                'Рекомендуется давать более развернутые ответы',
                'Добавьте больше конкретных примеров'
            ],
            'tips': [
                'Используйте метод STAR (Ситуация-Задача-Действие-Результат)',
                'Подготовьте 3-5 ключевых примеров из вашего опыта',
                'Изучите компанию перед собеседованием'
            ],
            'common_mistakes': [
                'Слишком короткие ответы',
                'Отсутствие конкретных цифр и результатов'
            ],
            'improvement_areas': [
                'Развитие навыков структурирования ответов',
                'Работа над уверенностью самопрезентации'
            ],
            'summary': 'Хорошая основа для дальнейшего развития навыков собеседования.'
        }