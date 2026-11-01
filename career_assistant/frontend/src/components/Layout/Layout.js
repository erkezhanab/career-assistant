// Общий каркас всех внутренних страниц.
//
// Содержит шапку и боковое меню, которые остаются на месте
// при переходах между разделами, а меняется только содержимое
// в центре — его подставляет компонент <Outlet />.

import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Box, Container, CssBaseline } from '@mui/material';
import Header from './Header';
import Sidebar from './Sidebar';

const Layout = () => {
  // Состояние бокового меню. Нужно только для телефонов:
  // на больших экранах меню видно всегда
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const toggleSidebar = () => {
    // Переключаем на противоположное значение
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      <CssBaseline />

      {/* Функция передаётся в шапку: кнопка-гамбургер открывает меню */}
      <Header toggleSidebar={toggleSidebar} />
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <Box
        component="main"
        sx={{
          flexGrow: 1,   // занять всё оставшееся место
          p: 3,
          mt: 8,         // отступ сверху, чтобы содержимое не ушло под шапку
          // Объект вместо числа — адаптивность: на экранах от размера sm
          // ширина уменьшается на 240px, место занимает боковое меню.
          // На телефонах меню скрыто и содержимое занимает всю ширину
          width: { sm: `calc(100% - 240px)` },
          ml: { sm: '240px' },
        }}
      >
        <Container maxWidth="xl">
          {/* Сюда react-router подставляет компонент текущей страницы
              (Dashboard, ResumePage, VacanciesPage и т.д.) */}
          <Outlet />
        </Container>
      </Box>
    </Box>
  );
};

export default Layout;
