// Защита административного раздела.
//
// Обёртка вокруг страницы админ-панели: пропускает только
// суперпользователя, остальным показывает сообщение об отказе.
//
// Права проверяются ЗАПРОСОМ К СЕРВЕРУ, а не по данным из localStorage:
// содержимое localStorage пользователь может изменить сам через
// инструменты разработчика, а ответ сервера подделать нельзя.
//
// Это дополнительный уровень защиты. Основной — на backend:
// все административные эндпоинты закрыты правилом IsAdminUser
// и отвечают 403, даже если страницу удалось открыть.

import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { CircularProgress, Box, Alert } from '@mui/material';
import { authAPI } from '../../api/auth';

const AdminRoute = ({ children }) => {
  // null = проверка ещё не завершена, true/false = результат проверки
  const [isAdmin, setIsAdmin] = useState(null);
  const [loading, setLoading] = useState(true);

  // Проверка выполняется один раз при открытии страницы
  useEffect(() => {
    checkAdminStatus();
  }, []);

  const checkAdminStatus = async () => {
    try {
      // getUserInfo() обращается к /auth/user-info/ — единственному
      // эндпоинту, который возвращает флаг прав is_superuser
      const userInfo = await authAPI.getUserInfo();
      setIsAdmin(Boolean(userInfo?.is_superuser));
    } catch (error) {
      // При любой ошибке доступ запрещаем: безопаснее отказать,
      // чем открыть раздел из-за сбоя сети
      console.error('Error checking admin status:', error);
      setIsAdmin(false);
    } finally {
      // finally выполнится в любом случае — индикатор загрузки
      // не «зависнет» даже при ошибке
      setLoading(false);
    }
  };

  // Пока идёт проверка, показываем индикатор загрузки
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  // Прав нет — объясняем причину вместо пустой страницы
  if (!isAdmin) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          У вас нет прав для доступа к этой странице. Только администраторы могут просматривать эту панель.
        </Alert>
      </Box>
    );
  }

  // Проверка пройдена — показываем саму страницу
  return children;
};

export default AdminRoute;
