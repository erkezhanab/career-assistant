// Контекст аутентификации — хранит данные текущего пользователя
// и делает их доступными всему приложению.
//
// Зачем нужен Context: без него данные о пользователе пришлось бы
// передавать через props из App в каждый компонент по цепочке.
// Контекст позволяет любому компоненту получить их напрямую
// вызовом useAuth().

import React, { createContext, useState, useContext, useEffect } from 'react';
import { authAPI } from '../api/auth';
import { toast } from 'react-toastify';

// Само хранилище. Создаётся с пустым значением по умолчанию
const AuthContext = createContext({});

// Свой хук-сокращение: вместо useContext(AuthContext)
// компоненты пишут просто useAuth()
export const useAuth = () => useContext(AuthContext);

// Компонент-обёртка. В App.js он оборачивает всё приложение,
// поэтому данные пользователя доступны на любой странице
export const AuthProvider = ({ children }) => {
  // null = пользователь не вошёл в систему
  const [user, setUser] = useState(null);
  // loading=true, пока проверяется сохранённый токен
  const [loading, setLoading] = useState(true);

  // useEffect с пустым массивом зависимостей [] выполняется
  // один раз при запуске приложения
  useEffect(() => {
    checkAuth();
  }, []);

  // Проверка сохранённого входа: благодаря ей пользователь
  // остаётся в системе после перезагрузки страницы
  const checkAuth = async () => {
    const token = localStorage.getItem('access_token');
    if (token) {
      try {
        // Токен может быть просрочен, поэтому проверяем его
        // настоящим запросом к серверу
        const response = await authAPI.getProfile();
        setUser(response.data);
      } catch (error) {
        // Токен недействителен — удаляем, чтобы не повторять
        // неудачные запросы при каждом открытии страницы
        console.error('Auth check failed:', error);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      }
    }
    // Проверка завершена — приложение можно отрисовывать
    setLoading(false);
  };

  const login = async (email, password) => {
    try {
      const response = await authAPI.login({ email, password });

      // Сохраняем оба токена: access — для запросов,
      // refresh — для продления сессии
      localStorage.setItem('access_token', response.data.access);
      localStorage.setItem('refresh_token', response.data.refresh);

      // Отдельный запрос за профилем: ответ на вход содержит
      // только токены, без имени и настроек пользователя
      const userResponse = await authAPI.getProfile();
      setUser(userResponse.data);

      toast.success('Вход выполнен успешно!');
      // Возвращаем результат объектом, чтобы страница входа
      // сама решила, перенаправлять пользователя или нет
      return { success: true };
    } catch (error) {
      // ?. (опциональная цепочка) защищает от ошибки, если
      // ответа от сервера нет вообще (например, нет интернета)
      toast.error(error.response?.data?.error || 'Ошибка входа');
      return {
        success: false,
        error: error.response?.data?.error || 'Ошибка входа'
      };
    }
  };

  const register = async (userData) => {
    try {
      const response = await authAPI.register(userData);

      // Backend выдаёт токены сразу при регистрации,
      // поэтому отдельный вход не требуется
      localStorage.setItem('access_token', response.data.access);
      localStorage.setItem('refresh_token', response.data.refresh);

      setUser(response.data.user);

      toast.success('Регистрация успешна!');
      return { success: true };
    } catch (error) {
      // Backend возвращает ошибки по полям:
      // { "email": ["Пользователь уже существует"], "password": [...] }
      const errors = error.response?.data;
      if (errors) {
        // Двойной цикл: по полям, затем по сообщениям каждого поля —
        // так пользователь увидит все ошибки формы сразу
        Object.values(errors).forEach(errorArray => {
          errorArray.forEach(errorMessage => {
            toast.error(errorMessage);
          });
        });
      } else {
        toast.error('Ошибка регистрации');
      }
      return {
        success: false,
        error: error.response?.data || 'Ошибка регистрации'
      };
    }
  };

  const logout = () => {
    authAPI.logout();   // удаляет токены
    setUser(null);
    toast.info('Вы вышли из системы');
    // Полная перезагрузка страницы, а не навигация роутером:
    // так гарантированно очищается состояние всех компонентов
    window.location.href = '/login';
  };

  const updateProfile = async (data) => {
    try {
      const response = await authAPI.updateProfile(data);
      // Обновляем данные в контексте, чтобы новое имя
      // сразу появилось в шапке сайта
      setUser(response.data);
      toast.success('Профиль обновлен');
      return { success: true };
    } catch (error) {
      toast.error('Ошибка обновления профиля');
      return { success: false };
    }
  };

  // Всё, что становится доступным через useAuth()
  const value = {
    user,
    login,
    register,
    logout,
    updateProfile,
    loading,
    checkAuth
  };

  return (
    <AuthContext.Provider value={value}>
      {/* Приложение отрисовывается только после проверки токена.
          Иначе защищённые страницы на мгновение сочли бы
          пользователя неавторизованным и перебросили на вход */}
      {!loading && children}
    </AuthContext.Provider>
  );
};
