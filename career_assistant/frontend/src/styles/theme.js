// Единая тема оформления Material UI.
//
// Задаёт цвета, шрифты и скругления для ВСЕХ компонентов приложения.
// Благодаря теме цвета не прописываются в каждом компоненте вручную:
// там указывается роль ("primary.main", "error.main"), а конкретный
// оттенок берётся отсюда. Поменять фирменный цвет всего сайта
// можно правкой одной строки.
//
// Подключается в App.js через <ThemeProvider theme={theme}>.

import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  // ЦВЕТОВАЯ ПАЛИТРА
  palette: {
    primary: {
      main: '#2563eb',    // основной синий: кнопки, активные пункты меню
      light: '#60a5fa',   // светлый оттенок: подсветка при наведении
      dark: '#1d4ed8',    // тёмный: состояние нажатия
    },
    secondary: {
      main: '#7c3aed',    // дополнительный фиолетовый
      light: '#a78bfa',
      dark: '#5b21b6',
    },
    // Смысловые цвета: используются для статусов и уведомлений
    success: {
      main: '#10b981',    // зелёный: успех, одобренное резюме
    },
    warning: {
      main: '#f59e0b',    // оранжевый: предупреждения, админ-панель
    },
    error: {
      main: '#ef4444',    // красный: ошибки, отклонённые отклики
    },
    background: {
      default: '#f8fafc', // фон страницы (светло-серый)
      paper: '#ffffff',   // фон карточек и панелей (белый)
    },
  },

  // ШРИФТЫ
  typography: {
    // Список шрифтов с запасными вариантами: если Inter
    // не установлен, браузер возьмёт следующий по порядку
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    // Заголовки делаются более жирными, чем по умолчанию,
    // чтобы структура страницы читалась лучше
    h1: { fontWeight: 700 },
    h2: { fontWeight: 700 },
    h3: { fontWeight: 600 },
    h4: { fontWeight: 600 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
  },

  // Скругление углов по умолчанию для всех элементов
  shape: {
    borderRadius: 8,
  },

  // ПЕРЕОПРЕДЕЛЕНИЕ СТИЛЕЙ ОТДЕЛЬНЫХ КОМПОНЕНТОВ
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          // Material UI по умолчанию пишет текст кнопок КАПСОМ —
          // отключаем, чтобы надписи читались обычным текстом
          textTransform: 'none',
          fontWeight: 500,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          // Мягкая тень вместо стандартной резкой —
          // карточки выглядят аккуратнее
          boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
          borderRadius: 12,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          // Скругление полей ввода под общий стиль интерфейса
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
          },
        },
      },
    },
  },
});

export default theme;
