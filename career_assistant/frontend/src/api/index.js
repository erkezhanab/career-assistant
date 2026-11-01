// Единая точка импорта всех API-модулей.
//
// Благодаря этому файлу компоненты пишут один импорт:
//   import { vacanciesAPI, applicationsAPI } from '../api';
// вместо отдельного импорта из каждого файла.

export { authAPI } from './auth';                   // вход, регистрация, профиль
export { resumesAPI } from './resumes';             // резюме и их анализ
export { vacanciesAPI } from './vacancies';         // поиск вакансий
export { applicationsAPI } from './applications';   // отклики и письма
export { interviewsAPI } from './interviews';       // пробные собеседования
export { adminAPI } from './adminAPI';              // административные функции

// default as — у testingAPI экспорт по умолчанию,
// поэтому при реэкспорте ему явно задаётся имя
export { default as testingAPI } from './testingAPI';
