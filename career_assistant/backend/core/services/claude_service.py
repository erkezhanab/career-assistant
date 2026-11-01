"""
Сервис искусственного интеллекта на базе Claude (Anthropic).

Это «мозг» проекта: все функции с ИИ вызывают методы этого класса.
  - analyze_resume             — оценка резюме по 6 критериям
  - generate_cover_letter      — сопроводительное письмо в 4 стилях
  - generate_interview_questions — вопросы для пробного собеседования
  - generate_test_questions    — персональные тестовые вопросы по резюме
  - analyze_interview_answers  — разбор ответов кандидата

Принцип работы одинаков для всех методов:
  1) собрать текстовый запрос (промпт) с данными пользователя;
  2) отправить его модели Claude;
  3) разобрать ответ (обычно JSON) и вернуть готовую структуру;
  4) при любой ошибке вернуть запасной ответ, чтобы приложение не падало.
"""

import json
import os
import random

import anthropic
from django.conf import settings


class ClaudeService:
    """
    Если ANTHROPIC_API_KEY не задан, сервис работает в демо-режиме:
    вместо реального вызова Claude отдаёт заранее подготовленные
    реалистичные ответы (для демонстрации интерфейса без ключа/оплаты).
    """

    # Версия модели вынесена в константу класса — меняется в одном месте
    MODEL = 'claude-sonnet-5'

    def __init__(self):
        """Подготавливает клиента API и определяет режим работы."""
        # Ключ ищем сначала в настройках Django, затем в переменных окружения
        api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)

        if not api_key:
            api_key = os.environ.get('ANTHROPIC_API_KEY')

        # Ключа нет -> демо-режим. Важно: класс НЕ бросает исключение,
        # иначе без ключа падали бы все страницы с ИИ-функциями
        self.demo_mode = not bool(api_key)
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else None

    def _generate(self, prompt, max_tokens=2048):
        """
        Низкоуровневый вызов модели: отправляет промпт и возвращает текст ответа.

        Вынесен отдельно, чтобы не дублировать код обращения к API
        в каждом из пяти публичных методов.
        """
        response = self.client.messages.create(
            model=self.MODEL,
            # Ограничение длины ответа: защита от слишком дорогих запросов
            max_tokens=max_tokens,
            # Формат диалога: роль 'user' — наш запрос к модели
            messages=[{'role': 'user', 'content': prompt}],
        )
        # Ответ приходит списком блоков; берём текст первого из них
        return response.content[0].text

    def _parse_json_response(self, response_text):
        """
        Превращает ответ модели в Python-объект (словарь или список).

        Нужен потому, что модель часто оборачивает JSON в markdown-блок
        ```json ... ```, и такую строку json.loads() прочитать не может.
        """
        response_text = response_text.strip()

        # Срезаем открывающую обёртку markdown
        if response_text.startswith('```json'):
            response_text = response_text[7:]   # длина строки '```json'
        elif response_text.startswith('```'):
            response_text = response_text[3:]

        # Срезаем закрывающую обёртку
        if response_text.endswith('```'):
            response_text = response_text[:-3]

        # Убираем случайные кавычки и переносы строк по краям
        response_text = response_text.strip('"\' \n')

        return json.loads(response_text)

    def analyze_resume(self, text, job_title=None):
        """
        Анализ резюме — оценка по 6 критериям.

        Параметры:
            text      — текст резюме, извлечённый из PDF/DOCX
            job_title — специализация пользователя (анализ под конкретную должность)

        Возвращает словарь: оценка, сильные стороны, что улучшить,
        что добавить, советы по формату, ключевые навыки.
        Вызывается из resumes/views.py в фоновом потоке после загрузки файла.
        """
        if self.demo_mode:
            return self._demo_analyze_resume(job_title)

        # Обрезаем длинные резюме: модель принимает ограниченный объём текста,
        # и чем длиннее запрос, тем дороже и дольше обработка
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
            response_text = self._generate(prompt)
            return self._parse_json_response(response_text)
        # Два разных сценария сбоя обрабатываются отдельно:
        except json.JSONDecodeError as e:
            # 1) модель ответила, но не корректным JSON
            print(f"JSON parsing error: {e}")
            return self._get_default_analysis(f"Ошибка парсинга JSON: {e}")
        except Exception as e:
            # 2) API недоступен, закончились лимиты, нет интернета и т.п.
            print(f"Claude API error: {e}")
            return self._get_default_analysis(str(e))

    def generate_cover_letter(self, resume_text, vacancy_text, style='formal'):
        """
        Генерация сопроводительного письма под конкретную вакансию.

        Сопоставляет резюме кандидата с описанием вакансии и пишет письмо
        в одном из 4 стилей. Вызывается из applications/views.py.
        Возвращает готовый текст (не JSON).
        """
        if self.demo_mode:
            return self._demo_cover_letter(style)

        # Описание стиля подставляется в промпт — именно это
        # заставляет модель менять тон письма
        styles_map = {
            'formal': 'официальный, профессиональный',
            'friendly': 'дружелюбный, теплый',
            'brief': 'краткий, по делу',
            'creative': 'креативный, нестандартный',
        }

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

        Длина: 200-300 слов. Выведи только текст письма, без пояснений.
        """

        try:
            return self._generate(prompt)
        except Exception as e:
            print(f"Error generating cover letter: {e}")
            return "Не удалось сгенерировать сопроводительное письмо. Пожалуйста, напишите его самостоятельно."

    def generate_interview_questions(self, resume_text, interview_type, vacancy_text=None):
        """
        Генерация 8-10 вопросов для пробного собеседования.

        Параметры:
            resume_text    — чтобы вопросы были про реальный опыт кандидата
            interview_type — hr / technical / stress / behavioral
            vacancy_text   — необязательно: вопросы под конкретную вакансию

        Возвращает список словарей: вопрос, категория, подсказка для ответа.
        """
        if self.demo_mode:
            return self._demo_interview_questions(interview_type)

        # Расшифровка типа интервью для модели: от неё зависит характер вопросов
        type_map = {
            'hr': 'HR интервью (общие вопросы о мотивации, опыте, карьерных целях)',
            'technical': 'Техническое интервью (вопросы по навыкам, технологиям, решению задач)',
            'stress': 'Стресс-интервью (сложные и провокационные вопросы)',
            'behavioral': 'Поведенческое интервью (ситуационные вопросы по опыту)',
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
            response_text = self._generate(prompt)
            return self._parse_json_response(response_text)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error for questions: {e}")
            return []
        except Exception as e:
            print(f"Error generating questions: {e}")
            return []

    def _get_default_analysis(self, error_message=""):
        """
        Запасной ответ, если анализ резюме не удался.

        Благодаря ему страница резюме всегда что-то показывает,
        а не падает с ошибкой при недоступности ИИ.
        """
        return {
            "overall_score": 5.0,
            "strong_points": ["Резюме требует анализа"],
            "improvements": ["Загрузите резюме для анализа"],
            "additions": ["Добавьте больше информации"],
            "format_recommendations": ["Используйте стандартный формат"],
            "key_skills": [],
            "summary": f"Требуется анализ ИИ. Ошибка: {error_message}" if error_message else "Требуется анализ ИИ",
        }

    # --- Демо-ответы (используются, когда ANTHROPIC_API_KEY не задан) ---
    # Нужны, чтобы проект можно было показать и протестировать без
    # оплаченного ключа API: интерфейс работает полностью, данные —
    # заранее подготовленные и помеченные как демонстрационные.

    def _demo_analyze_resume(self, job_title=None):
        """Демо-анализ резюме: случайный из двух готовых вариантов."""
        variants = [
            {
                "overall_score": 7.8,
                "strong_points": [
                    "Чёткая структура резюме, легко читается",
                    "Указаны конкретные технологии и инструменты",
                    "Есть количественные результаты по части проектов",
                ],
                "improvements": [
                    "Добавьте больше цифр и метрик (%, сроки, количество пользователей)",
                    "Раздел о достижениях можно сделать более конкретным",
                ],
                "additions": [
                    "Ссылки на портфолио или GitHub",
                    "Краткое summary в начале резюме (2-3 предложения о себе)",
                ],
                "format_recommendations": [
                    "Используйте единый шрифт и отступы по всему документу",
                    "Выделите ключевые навыки в отдельный блок",
                ],
                "key_skills": ["Python", "Django", "PostgreSQL", "REST API", "Git"],
                "summary": "Хорошее резюме среднего уровня. Чтобы выделиться среди конкурентов, добавьте измеримые результаты и портфолио. (Демо-ответ, ИИ не подключен)",
            },
            {
                "overall_score": 6.4,
                "strong_points": [
                    "Релевантный опыт для указанной специализации",
                    "Аккуратное оформление без лишней информации",
                ],
                "improvements": [
                    "Слишком общие формулировки обязанностей — замените на результаты",
                    "Не хватает информации об образовании/курсах",
                ],
                "additions": [
                    "Сертификаты и пройденные курсы",
                    "Уровень владения языками (если есть международный опыт)",
                ],
                "format_recommendations": [
                    "Сократите резюме до 1-2 страниц",
                    "Используйте маркированные списки вместо сплошного текста",
                ],
                "key_skills": ["JavaScript", "React", "TypeScript", "Git"],
                "summary": "Резюме нуждается в доработке формулировок достижений. (Демо-ответ, ИИ не подключен)",
            },
        ]
        # random.choice — чтобы при повторных загрузках резюме
        # результат отличался и демонстрация выглядела живой
        result = random.choice(variants)
        if job_title:
            # dict(result) создаёт копию: без неё мы бы испортили
            # исходный словарь из списка variants для следующих вызовов
            result = dict(result)
            result["summary"] = f"[{job_title}] " + result["summary"]
        return result

    def _demo_cover_letter(self, style='formal'):
        """Демо-письма: по одному готовому образцу на каждый стиль."""
        letters = {
            'formal': (
                "Уважаемые коллеги!\n\n"
                "Меня заинтересовала открытая вакансия в вашей компании. Имею опыт работы "
                "по смежному профилю и уверен, что мои навыки и подход к задачам будут полезны "
                "вашей команде.\n\n"
                "За время работы я участвовал в разработке и поддержке проектов, решал технические "
                "задачи различной сложности и постоянно развивал профессиональные компетенции. "
                "Готов обсудить детали сотрудничества на собеседовании.\n\n"
                "Благодарю за уделённое время и рассмотрение моей кандидатуры.\n\n"
                "С уважением.\n\n"
                "(Демо-письмо: показан пример формата без подключения ИИ)"
            ),
            'friendly': (
                "Привет!\n\n"
                "Увидел вашу вакансию и очень захотелось откликнуться — то, что вы ищете, "
                "хорошо совпадает с тем, что я умею и люблю делать.\n\n"
                "За последние годы я набрался опыта в решении похожих задач, умею работать в команде "
                "и быстро разбираюсь в новых технологиях. Буду рад обсудить, как я могу быть полезен "
                "вашему проекту.\n\n"
                "Спасибо, что дочитали до конца! Жду обратной связи.\n\n"
                "(Демо-письмо: показан пример формата без подключения ИИ)"
            ),
            'brief': (
                "Здравствуйте!\n\n"
                "Откликаюсь на вакансию. Опыт соответствует требованиям, готов приступить к работе "
                "в короткие сроки. Резюме прилагаю, буду рад обсудить детали на интервью.\n\n"
                "С уважением.\n\n"
                "(Демо-письмо: показан пример формата без подключения ИИ)"
            ),
            'creative': (
                "Здравствуйте!\n\n"
                "Если бы резюме могло танцевать, моё бы точно начало именно на этом месте — "
                "настолько точно вакансия совпадает с тем, что я умею.\n\n"
                "За плечами — реальные задачи, реальные решения и искреннее желание расти вместе "
                "с командой, а не просто \"закрывать тикеты\". Готов показать на деле, а не только "
                "на бумаге.\n\n"
                "Жду возможности познакомиться лично!\n\n"
                "(Демо-письмо: показан пример формата без подключения ИИ)"
            ),
        }
        # Второй аргумент .get() — значение по умолчанию:
        # если стиль неизвестен, вернём официальное письмо
        return letters.get(style, letters['formal'])

    def _demo_interview_questions(self, interview_type):
        """Демо-вопросы собеседования: готовый набор под каждый тип интервью."""
        questions_by_type = {
            'hr': [
                {"question": "Расскажите немного о себе и своём профессиональном пути.", "category": "Общее", "tips": "Коротко: опыт, ключевые навыки, что ищете дальше."},
                {"question": "Почему вы хотите работать именно в нашей компании?", "category": "Мотивация", "tips": "Покажите, что изучили компанию и её продукт."},
                {"question": "Какие ваши сильные и слабые стороны?", "category": "Самооценка", "tips": "Выберите реальную слабость и расскажите, как с ней работаете."},
                {"question": "Расскажите о ситуации, когда вам пришлось работать в команде над сложной задачей.", "category": "Опыт", "tips": "Используйте структуру STAR."},
                {"question": "Где вы видите себя через 3 года?", "category": "Карьерные цели", "tips": "Свяжите ответ с ростом внутри компании."},
                {"question": "Как вы реагируете на критику?", "category": "Личные качества", "tips": "Приведите конкретный пример и результат."},
            ],
            'technical': [
                {"question": "Расскажите о самом сложном техническом проекте в вашем опыте.", "category": "Опыт", "tips": "Опишите задачу, решение и результат."},
                {"question": "Как вы подходите к оптимизации производительности приложения?", "category": "Технические навыки", "tips": "Упомяните профилирование и конкретные метрики."},
                {"question": "Расскажите, как вы проектируете структуру базы данных для нового проекта.", "category": "Архитектура", "tips": "Говорите о нормализации, индексах, связях."},
                {"question": "Как вы тестируете свой код перед релизом?", "category": "Качество кода", "tips": "Упомяните unit-тесты, code review, CI/CD."},
                {"question": "Опишите случай, когда вам пришлось исправлять баг в продакшене.", "category": "Проблемные ситуации", "tips": "Расскажите про диагностику и предотвращение повторения."},
            ],
            'stress': [
                {"question": "Почему мы должны выбрать именно вас, а не другого кандидата?", "category": "Давление", "tips": "Отвечайте спокойно и по фактам, без извинений."},
                {"question": "Расскажите о своей самой крупной профессиональной неудаче.", "category": "Самокритика", "tips": "Честно, но с акцентом на извлечённый урок."},
                {"question": "Что вы будете делать, если за один день на вас упадёт сразу 5 горящих задач?", "category": "Приоритизация", "tips": "Опишите алгоритм приоритизации."},
                {"question": "Как вы отреагируете, если руководитель публично усомнится в вашей компетентности?", "category": "Эмоциональная устойчивость", "tips": "Сохраняйте профессионализм и конкретику."},
            ],
            'behavioral': [
                {"question": "Расскажите о случае, когда вы не согласились с решением руководителя.", "category": "Конфликты", "tips": "Используйте STAR, покажите уважительную аргументацию."},
                {"question": "Приведите пример, когда вам нужно было быстро обучиться новому навыку.", "category": "Обучаемость", "tips": "Расскажите про подход к обучению и итог."},
                {"question": "Опишите ситуацию, где вы проявили лидерство без формальной должности.", "category": "Лидерство", "tips": "Фокус на влиянии на результат команды."},
                {"question": "Расскажите про случай, когда вам нужно было уложиться в жёсткий дедлайн.", "category": "Тайм-менеджмент", "tips": "Опишите, как вы спланировали работу."},
            ],
        }
        return questions_by_type.get(interview_type, questions_by_type['hr'])

    def generate_test_questions(self, resume_text, category="general", difficulty="medium", count=15):
        """
        Генерация персональных тестовых вопросов на основе резюме.

        Ключевая идея: тест проверяет именно те навыки, которые кандидат
        указал в резюме, а сложность подбирается по его опыту работы.

        Параметры:
            category   — направление теста (programming, design, ...)
            difficulty — easy / medium / hard (считается из стажа)
            count      — сколько вопросов сгенерировать

        Возвращает список вопросов, готовый к сохранению в модель TestQuestion.
        """
        if self.demo_mode:
            return self._get_default_test_questions(category, count)

        # Словари-«переводчики»: короткий код -> понятное модели описание
        category_map = {
            'programming': 'Программирование и разработка ПО',
            'data_science': 'Наука о данных и машинное обучение',
            'design': 'Дизайн и UX/UI',
            'marketing': 'Маркетинг и продвижение',
            'management': 'Управление и менеджмент',
            'analytics': 'Аналитика и бизнес-анализ',
            'testing': 'Тестирование и QA',
            'devops': 'DevOps и инфраструктура',
            'general': 'Общие профессиональные вопросы',
        }

        difficulty_map = {
            'easy': 'легкий (для Junior специалистов)',
            'medium': 'средний (для Middle специалистов)',
            'hard': 'сложный (для Senior специалистов)',
        }

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
            # max_tokens больше обычного: 15 вопросов с вариантами
            # ответов и пояснениями не поместятся в 2048 токенов
            response_text = self._generate(prompt, max_tokens=4096)
            data = self._parse_json_response(response_text)

            # Приводим ответ модели к формату полей модели TestQuestion
            formatted_questions = []
            for q in data.get('questions', []):
                # В базе correct_answer — текстовое поле, а для вопросов
                # с несколькими ответами это список. Поэтому список
                # сохраняем JSON-строкой, чтобы потом развернуть обратно
                if isinstance(q['correct_answer'], list):
                    correct_answer = json.dumps(q['correct_answer'])
                else:
                    correct_answer = str(q['correct_answer'])

                formatted_questions.append({
                    'question_text': q['question_text'],
                    'question_type': q['question_type'],
                    'options': q.get('options', []),
                    'correct_answer': correct_answer,
                    'explanation': q.get('explanation', ''),
                    'difficulty': q.get('difficulty', 3),
                    'skill_category': q.get('skill_category', 'general'),
                })

            return formatted_questions

        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга JSON для тестовых вопросов: {e}")
            return self._get_default_test_questions(category, count)
        except Exception as e:
            print(f"Ошибка генерации тестовых вопросов: {e}")
            return self._get_default_test_questions(category, count)

    def _get_default_test_questions(self, category, count):
        """
        Банк готовых вопросов по направлениям.

        Используется в двух случаях: в демо-режиме и когда ИИ не ответил —
        тест всё равно можно пройти.
        """
        # Ключи соответствуют значениям, которые возвращает
        # StartTestView._detect_specialization (frontend, backend, database,
        # devops, data_science, general) — иначе подобрался бы
        # общий вопрос вместо вопросов по специальности
        bank = {
            'frontend': [
                {
                    'question_text': 'Что произойдёт при вызове setState в React?',
                    'question_type': 'single_choice',
                    'options': ['Компонент перерисуется', 'Страница перезагрузится',
                                'Ничего не произойдёт', 'Удалится состояние'],
                    'correct_answer': 'Компонент перерисуется',
                    'explanation': 'Изменение состояния запускает повторный рендер компонента.',
                    'difficulty': 2,
                    'skill_category': 'React',
                },
                {
                    'question_text': 'Какие хуки существуют в React?',
                    'question_type': 'multiple_choice',
                    'options': ['useState', 'useEffect', 'useQuery', 'useMemo'],
                    'correct_answer': ['useState', 'useEffect', 'useMemo'],
                    'explanation': 'useQuery — это хук библиотеки React Query, а не самого React.',
                    'difficulty': 3,
                    'skill_category': 'React',
                },
                {
                    'question_text': 'Чем отличается let от var в JavaScript?',
                    'question_type': 'open_ended',
                    'options': [],
                    'correct_answer': 'let имеет блочную область видимости',
                    'explanation': 'var видна во всей функции, let — только внутри блока {}.',
                    'difficulty': 3,
                    'skill_category': 'JavaScript',
                },
                {
                    'question_text': 'Что такое virtual DOM?',
                    'question_type': 'single_choice',
                    'options': ['Копия DOM в памяти для быстрого сравнения',
                                'Браузерный API', 'База данных', 'CSS-препроцессор'],
                    'correct_answer': 'Копия DOM в памяти для быстрого сравнения',
                    'explanation': 'React сравнивает virtual DOM с реальным и обновляет только изменения.',
                    'difficulty': 3,
                    'skill_category': 'React',
                },
            ],
            'backend': [
                {
                    'question_text': 'Что делает метод select_related в Django ORM?',
                    'question_type': 'single_choice',
                    'options': ['Загружает связанные объекты одним запросом',
                                'Удаляет связанные объекты', 'Создаёт индекс', 'Фильтрует поля'],
                    'correct_answer': 'Загружает связанные объекты одним запросом',
                    'explanation': 'select_related решает проблему N+1 запросов через SQL JOIN.',
                    'difficulty': 3,
                    'skill_category': 'Django ORM',
                },
                {
                    'question_text': 'Какие HTTP-методы считаются идемпотентными?',
                    'question_type': 'multiple_choice',
                    'options': ['GET', 'POST', 'PUT', 'DELETE'],
                    'correct_answer': ['GET', 'PUT', 'DELETE'],
                    'explanation': 'POST не идемпотентен: повторный вызов создаёт новую запись.',
                    'difficulty': 3,
                    'skill_category': 'REST API',
                },
                {
                    'question_text': 'Что такое миграция базы данных?',
                    'question_type': 'single_choice',
                    'options': ['Версионируемое изменение структуры БД', 'Перенос сервера',
                                'Резервная копия', 'Очистка кеша'],
                    'correct_answer': 'Версионируемое изменение структуры БД',
                    'explanation': 'Миграции позволяют воспроизводить изменения схемы на любом окружении.',
                    'difficulty': 2,
                    'skill_category': 'Базы данных',
                },
                {
                    'question_text': 'Для чего используется кеширование в веб-приложении?',
                    'question_type': 'open_ended',
                    'options': [],
                    'correct_answer': 'для ускорения ответа и снижения нагрузки',
                    'explanation': 'Кеш позволяет не выполнять повторно дорогие запросы и вычисления.',
                    'difficulty': 2,
                    'skill_category': 'Производительность',
                },
            ],
            'database': [
                {
                    'question_text': 'Для чего нужен индекс в базе данных?',
                    'question_type': 'single_choice',
                    'options': ['Для ускорения поиска по полю', 'Для шифрования данных',
                                'Для резервного копирования', 'Для сжатия таблицы'],
                    'correct_answer': 'Для ускорения поиска по полю',
                    'explanation': 'Индекс ускоряет чтение, но замедляет запись и занимает место.',
                    'difficulty': 2,
                    'skill_category': 'SQL',
                },
                {
                    'question_text': 'Какие типы JOIN существуют в SQL?',
                    'question_type': 'multiple_choice',
                    'options': ['INNER JOIN', 'LEFT JOIN', 'MERGE JOIN', 'FULL OUTER JOIN'],
                    'correct_answer': ['INNER JOIN', 'LEFT JOIN', 'FULL OUTER JOIN'],
                    'explanation': 'MERGE JOIN — это алгоритм выполнения, а не тип соединения в SQL.',
                    'difficulty': 3,
                    'skill_category': 'SQL',
                },
                {
                    'question_text': 'Что такое транзакция?',
                    'question_type': 'single_choice',
                    'options': ['Группа операций, выполняемых как одно целое',
                                'Запрос на чтение', 'Копия таблицы', 'Вид индекса'],
                    'correct_answer': 'Группа операций, выполняемых как одно целое',
                    'explanation': 'Транзакция либо применяется полностью, либо полностью отменяется.',
                    'difficulty': 3,
                    'skill_category': 'Базы данных',
                },
            ],
            'devops': [
                {
                    'question_text': 'Чем контейнер отличается от виртуальной машины?',
                    'question_type': 'single_choice',
                    'options': ['Контейнер использует ядро хоста, без своей ОС',
                                'Контейнер медленнее', 'Это одно и то же',
                                'Контейнер требует больше памяти'],
                    'correct_answer': 'Контейнер использует ядро хоста, без своей ОС',
                    'explanation': 'Поэтому контейнеры запускаются за секунды и легче по весу.',
                    'difficulty': 3,
                    'skill_category': 'Docker',
                },
                {
                    'question_text': 'Что входит в понятие CI/CD?',
                    'question_type': 'multiple_choice',
                    'options': ['Автоматическая сборка', 'Автоматические тесты',
                                'Ручное развёртывание', 'Автоматическое развёртывание'],
                    'correct_answer': ['Автоматическая сборка', 'Автоматические тесты',
                                       'Автоматическое развёртывание'],
                    'explanation': 'Смысл CI/CD — убрать ручные шаги из процесса поставки.',
                    'difficulty': 3,
                    'skill_category': 'CI/CD',
                },
                {
                    'question_text': 'Какая команда показывает запущенные контейнеры Docker?',
                    'question_type': 'single_choice',
                    'options': ['docker ps', 'docker build', 'docker rm', 'docker pull'],
                    'correct_answer': 'docker ps',
                    'explanation': 'docker ps выводит список работающих контейнеров.',
                    'difficulty': 1,
                    'skill_category': 'Docker',
                },
            ],
            'general': [
                {
                    'question_text': 'Что такое soft skills?',
                    'question_type': 'single_choice',
                    'options': ['Навыки работы с софтом', 'Профессиональные навыки',
                                'Гибкие навыки', 'Технические навыки'],
                    'correct_answer': 'Гибкие навыки',
                    'explanation': 'Soft skills — личные и социальные навыки: общение, работа в команде.',
                    'difficulty': 1,
                    'skill_category': 'Общее',
                },
                {
                    'question_text': 'Что из перечисленного относится к методологии Agile?',
                    'question_type': 'multiple_choice',
                    'options': ['Спринты', 'Ретроспектива', 'Диаграмма Ганта', 'Daily standup'],
                    'correct_answer': ['Спринты', 'Ретроспектива', 'Daily standup'],
                    'explanation': 'Диаграмма Ганта относится к каскадной модели управления.',
                    'difficulty': 2,
                    'skill_category': 'Agile',
                },
                {
                    'question_text': 'Для чего используется система контроля версий?',
                    'question_type': 'single_choice',
                    'options': ['Для хранения истории изменений кода', 'Для компиляции',
                                'Для тестирования', 'Для развёртывания'],
                    'correct_answer': 'Для хранения истории изменений кода',
                    'explanation': 'Git позволяет отслеживать изменения и работать над кодом в команде.',
                    'difficulty': 1,
                    'skill_category': 'Git',
                },
                {
                    'question_text': 'Как называется метод структурирования ответов на собеседовании?',
                    'question_type': 'open_ended',
                    'options': [],
                    'correct_answer': 'STAR',
                    'explanation': 'STAR: Situation, Task, Action, Result — ситуация, задача, действие, результат.',
                    'difficulty': 2,
                    'skill_category': 'Карьера',
                },
            ],
            'programming': [
                {
                    'question_text': 'Что такое переменная в программировании?',
                    'question_type': 'single_choice',
                    'options': ['Именованная область памяти', 'Функция', 'Класс', 'Метод'],
                    'correct_answer': 'Именованная область памяти',
                    'explanation': 'Переменная - это именованная область памяти, которая хранит данные.',
                    'difficulty': 1,
                    'skill_category': 'Основы программирования',
                },
                {
                    'question_text': 'Какие из этих языков являются статически типизированными?',
                    'question_type': 'multiple_choice',
                    'options': ['Java', 'Python', 'C++', 'JavaScript'],
                    'correct_answer': ['Java', 'C++'],
                    'explanation': 'Java и C++ - статически типизированные языки, Python и JavaScript - динамически типизированные.',
                    'difficulty': 2,
                    'skill_category': 'Языки программирования',
                },
                {
                    'question_text': 'Что из перечисленного относится к принципам ООП?',
                    'question_type': 'multiple_choice',
                    'options': ['Инкапсуляция', 'Наследование', 'Компиляция', 'Полиморфизм'],
                    'correct_answer': ['Инкапсуляция', 'Наследование', 'Полиморфизм'],
                    'explanation': 'Компиляция - это процесс сборки программы, а не принцип ООП.',
                    'difficulty': 2,
                    'skill_category': 'ООП',
                },
                {
                    'question_text': 'Чем отличается список (list) от кортежа (tuple) в Python?',
                    'question_type': 'open_ended',
                    'options': [],
                    'correct_answer': 'список изменяемый, кортеж неизменяемый',
                    'explanation': 'tuple является immutable структурой, list — mutable.',
                    'difficulty': 3,
                    'skill_category': 'Python',
                },
            ],
            'data_science': [
                {
                    'question_text': 'Какая библиотека Python чаще всего используется для работы с таблицами данных?',
                    'question_type': 'single_choice',
                    'options': ['pandas', 'flask', 'requests', 'pytest'],
                    'correct_answer': 'pandas',
                    'explanation': 'pandas предоставляет структуры DataFrame для анализа табличных данных.',
                    'difficulty': 1,
                    'skill_category': 'Data Science',
                },
                {
                    'question_text': 'Какие из перечисленных являются метриками качества классификации?',
                    'question_type': 'multiple_choice',
                    'options': ['Precision', 'Recall', 'MSE', 'F1-score'],
                    'correct_answer': ['Precision', 'Recall', 'F1-score'],
                    'explanation': 'MSE используется для регрессии, а не классификации.',
                    'difficulty': 3,
                    'skill_category': 'ML метрики',
                },
            ],
            'design': [
                {
                    'question_text': 'Что из перечисленного относится к принципам UX-дизайна?',
                    'question_type': 'multiple_choice',
                    'options': ['Согласованность', 'Обратная связь', 'Компиляция', 'Доступность'],
                    'correct_answer': ['Согласованность', 'Обратная связь', 'Доступность'],
                    'explanation': 'Компиляция относится к программированию, а не к UX.',
                    'difficulty': 2,
                    'skill_category': 'UX',
                },
                {
                    'question_text': 'Какой инструмент чаще всего используется для прототипирования интерфейсов?',
                    'question_type': 'single_choice',
                    'options': ['Figma', 'Excel', 'Postman', 'Jenkins'],
                    'correct_answer': 'Figma',
                    'explanation': 'Figma - популярный инструмент для UI/UX прототипирования.',
                    'difficulty': 1,
                    'skill_category': 'Инструменты',
                },
            ],
            'management': [
                {
                    'question_text': 'Что из перечисленного относится к методологии Agile?',
                    'question_type': 'multiple_choice',
                    'options': ['Спринты', 'Ретроспектива', 'Диаграмма Ганта', 'Daily standup'],
                    'correct_answer': ['Спринты', 'Ретроспектива', 'Daily standup'],
                    'explanation': 'Диаграмма Ганта чаще используется в классическом каскадном управлении проектами.',
                    'difficulty': 2,
                    'skill_category': 'Agile',
                },
            ],
        }

        questions = bank.get(category, [
            {
                'question_text': 'Что такое soft skills?',
                'question_type': 'single_choice',
                'options': ['Навыки работы с софтом', 'Профессиональные навыки', 'Гибкие навыки', 'Технические навыки'],
                'correct_answer': 'Гибкие навыки',
                'explanation': 'Soft skills (гибкие навыки) - это личные качества и социальные навыки, такие как коммуникация, работа в команде, лидерство.',
                'difficulty': 1,
                'skill_category': 'Общее',
            },
        ])

        # Если готовых вопросов меньше, чем запросили, размножаем список,
        # чтобы тест набрался до нужной длины
        if len(questions) < count:
            questions = questions * (count // len(questions) + 1)

        # Срез [:count] отдаёт ровно столько вопросов, сколько просили
        return questions[:count]

    def analyze_interview_answers(self, context):
        """
        Разбор ответов кандидата после пробного собеседования.

        Параметр context — словарь с типом интервью, списком вопросов,
        ответами пользователя и (опционально) описанием вакансии.

        Возвращает оценку (1-10), сильные и слабые стороны, советы,
        типичные ошибки и области развития. Вызывается из interviews/views.py.
        """
        if self.demo_mode:
            return self._get_default_feedback()

        # Промпт собирается по частям: сначала общая инструкция,
        # затем в цикле добавляются все пары «вопрос — ответ»
        prompt = f"""
        Ты - опытный HR-специалист, который проводит анализ собеседования кандидата.

        КОНТЕКСТ СОБЕСЕДОВАНИЯ:
        Тип собеседования: {context['interview_type']}

        ВОПРОСЫ И ОТВЕТЫ:
        """

        # zip() соединяет вопросы с ответами попарно, enumerate() даёт номер.
        # Если ответов меньше, чем вопросов, zip просто остановится — ошибки не будет
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
            response_text = self._generate(prompt)
            return self._parse_json_response(response_text)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error for feedback: {e}")
            return self._get_default_feedback()
        except Exception as e:
            print(f"Error analyzing interview answers: {e}")
            return self._get_default_feedback()

    def _get_default_feedback(self):
        """
        Универсальный разбор собеседования.

        Содержит советы, полезные любому кандидату (метод STAR, примеры
        из опыта). Используется в демо-режиме и при сбое ИИ.
        """
        return {
            'overall_score': 6.5,
            'strengths': [
                'Вы предоставили ответы на вопросы',
                'Показали заинтересованность в позиции',
            ],
            'weaknesses': [
                'Рекомендуется давать более развернутые ответы',
                'Добавьте больше конкретных примеров',
            ],
            'tips': [
                'Используйте метод STAR (Ситуация-Задача-Действие-Результат)',
                'Подготовьте 3-5 ключевых примеров из вашего опыта',
                'Изучите компанию перед собеседованием',
            ],
            'common_mistakes': [
                'Слишком короткие ответы',
                'Отсутствие конкретных цифр и результатов',
            ],
            'improvement_areas': [
                'Развитие навыков структурирования ответов',
                'Работа над уверенностью самопрезентации',
            ],
            'summary': 'Хорошая основа для дальнейшего развития навыков собеседования.',
        }
