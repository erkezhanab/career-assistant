// Вспомогательные функции общего назначения.
//
// Вынесены в отдельный файл, чтобы не дублировать одинаковый код
// форматирования дат и зарплат в разных компонентах.

// Приводит дату из API ("2026-11-01T10:00:00Z")
// к читаемому виду: "1 ноября 2026 г."
export const formatDate = (dateString) => {
  const date = new Date(dateString);
  // 'ru-RU' — русская локаль: месяцы по-русски и правильный порядок
  return date.toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
};

// Форматирует зарплату с учётом того, что одна из границ
// может быть не указана
export const formatSalary = (from, to, currency) => {
  // Зарплата не указана вообще
  if (!from && !to) return 'Не указана';

  // HeadHunter присылает код 'RUR', показываем привычный символ
  const formattedCurrency = currency === 'RUR' ? '₽' : currency;

  // Три варианта: указан диапазон, только «от», только «до»
  if (from && to) {
    return `${from} - ${to} ${formattedCurrency}`;
  } else if (from) {
    return `от ${from} ${formattedCurrency}`;
  } else if (to) {
    return `до ${to} ${formattedCurrency}`;
  }

  return 'Не указана';
};

// Обрезает длинный текст, добавляя многоточие.
// Применяется к описаниям вакансий в списке, чтобы карточки
// оставались одинаковой высоты
export const truncateText = (text, maxLength = 100) => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

// Проверка формата email на стороне браузера.
// Регулярное выражение требует: текст без пробелов, затем @,
// затем домен с точкой. Это предварительная проверка для удобства —
// основная выполняется на сервере
export const isValidEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
};

// Скачивание файла по ссылке.
// Приём со временной ссылкой: создаём невидимый элемент <a>,
// программно «щёлкаем» по нему и сразу удаляем. Это единственный
// способ запустить скачивание из JavaScript без перехода на другую страницу
export const downloadFile = (url, filename) => {
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;   // имя, под которым сохранится файл
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};
