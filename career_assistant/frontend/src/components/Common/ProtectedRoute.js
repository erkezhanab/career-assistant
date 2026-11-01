// Защита страниц от неавторизованного доступа.
//
// В App.js этот компонент оборачивает весь основной раздел сайта.
// Работает как «охранник»: пропускает дальше только тех,
// кто вошёл в систему, остальных отправляет на страницу входа.

import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Box, CircularProgress } from '@mui/material';

const ProtectedRoute = ({ children }) => {
  // Данные берутся из контекста авторизации
  const { user, loading } = useAuth();

  // Пока проверяется сохранённый токен, показываем индикатор загрузки.
  // Без этой проверки пользователя на мгновение выбрасывало бы
  // на страницу входа при каждой перезагрузке страницы
  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',   // по центру всего экрана
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  // Пользователь не вошёл — перенаправляем на страницу входа.
  // Navigate выполняет переход сразу при отрисовке компонента
  if (!user) {
    return <Navigate to="/login" />;
  }

  // Проверка пройдена — показываем запрошенную страницу
  return children;
};

export default ProtectedRoute;
