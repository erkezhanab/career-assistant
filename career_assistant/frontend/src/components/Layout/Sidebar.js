// Боковое меню навигации.
//
// Показывает список разделов и подсвечивает текущий. Пункт
// «Админ-панель» добавляется только суперпользователю.
//
// Отрисовывается в двух вариантах: выдвижное меню для телефонов
// и постоянно видимое для компьютеров (см. два Drawer в конце файла).

import React, { useState, useEffect } from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Box,
  Divider,
  Typography,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Description as DescriptionIcon,
  Work as WorkIcon,
  Forum as ForumIcon,
  Person as PersonIcon,
  Settings as SettingsIcon,
  Assignment as AssignmentIcon,
  AdminPanelSettings as AdminPanelIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { authAPI } from '../../api'; // Добавляем импорт API

// Разделы меню описаны массивом, а не набором повторяющейся разметки:
// чтобы добавить новый пункт, достаточно дописать объект сюда
const menuItems = [
  { text: 'Главная', icon: <DashboardIcon />, path: '/' },
  { text: 'Мои резюме', icon: <DescriptionIcon />, path: '/resumes' },
  { text: 'Поиск вакансий', icon: <WorkIcon />, path: '/vacancies' },
  { text: 'Подготовка к собеседованию', icon: <ForumIcon />, path: '/interviews' },
  { text: 'Тестирование', icon: <AssignmentIcon />, path: '/testing' },
  { text: 'Профиль', icon: <PersonIcon />, path: '/profile' },
  { text: 'Настройки', icon: <SettingsIcon />, path: '/settings' },
];

const Sidebar = ({ open, onClose }) => {
  const navigate = useNavigate();
  // useLocation даёт текущий адрес — по нему подсвечивается активный пункт
  const location = useLocation();
  const [user, setUser] = useState(null);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    loadUserInfo();
  }, []);

  const loadUserInfo = async () => {
    try {
      // Пробуем получить данные пользователя разными способами
      // Сначала из localStorage — чтобы не обращаться к серверу
      // при каждом переходе между страницами
      const userStr = localStorage.getItem('user');
      if (userStr) {
        const parsedUser = JSON.parse(userStr);
        setUser(parsedUser);
        setIsAdmin(parsedUser?.is_superuser || false);
      } else {
        // Если нет в localStorage, пытаемся получить через API
        const userInfo = await authAPI.getUserInfo();
        setUser(userInfo);
        setIsAdmin(userInfo?.is_superuser || false);
        // Сохраняем в localStorage
        // При выходе из системы эта запись удаляется (authAPI.logout),
        // поэтому следующий пользователь не увидит чужие данные
        localStorage.setItem('user', JSON.stringify(userInfo));
      }
    } catch (error) {
      console.error('Error loading user info:', error);
      // Устанавливаем дефолтные значения
      // Меню всё равно отрисуется, просто без имени пользователя
      setUser({ email: '', first_name: '', last_name: '' });
      setIsAdmin(false);
    }
  };

  // Админу добавляется дополнительный пункт меню.
  // Это удобство интерфейса, а не защита: сам раздел закрыт
  // компонентом AdminRoute и правами на backend
  const allMenuItems = isAdmin
    ? [...menuItems, { text: 'Админ-панель', icon: <AdminPanelIcon />, path: '/admin' }]
    : menuItems;

  // Разметка меню вынесена в переменную, так как используется
  // дважды — в мобильном и в постоянном варианте Drawer
  const drawer = (
    <Box sx={{ width: 240 }}>
      <Box sx={{ p: 3 }}>
        <Typography variant="h6" sx={{ fontWeight: 600, color: 'primary.main' }}>
          Career Assistant
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Ваш помощник в карьере
        </Typography>

        {/* Значок «Администратор». Запись вида {условие && (разметка)}
            означает: показать блок, только если условие истинно */}
        {isAdmin && (
          <Box sx={{ mt: 1 }}>
            <Typography
              variant="caption"
              sx={{
                bgcolor: 'warning.main',
                color: 'white',
                px: 1,
                py: 0.5,
                borderRadius: 1,
                fontWeight: 'bold'
              }}
            >
              Администратор
            </Typography>
          </Box>
        )}
      </Box>
      <Divider />
      <List>
        {/* map() превращает массив разделов в список пунктов меню.
            key обязателен — по нему React отслеживает элементы списка */}
        {allMenuItems.map((item) => (
          <ListItem
            button
            key={item.text}
            onClick={() => {
              navigate(item.path);
              onClose();   // на телефоне меню закрывается после перехода
            }}
            sx={{
              // Подсветка активного раздела: сравниваем адрес пункта
              // с текущим адресом страницы
              bgcolor: location.pathname === item.path ? 'primary.light' : 'transparent',
              color: location.pathname === item.path ? 'primary.contrastText' : 'inherit',
              '&:hover': {
                bgcolor: 'primary.light',
                color: 'primary.contrastText',
              },
              borderRadius: 1,
              mx: 1,
              my: 0.5,
              // Админ-панель выделяется рамкой, чтобы отличаться
              // от обычных разделов. ... добавляет стили только для неё
              ...(item.text === 'Админ-панель' && {
                border: '1px solid',
                borderColor: 'warning.main',
                '&:hover': {
                  bgcolor: 'warning.light',
                }
              }),
            }}
          >
            <ListItemIcon
              sx={{
                color: location.pathname === item.path ? 'primary.contrastText' : 'inherit',
                ...(item.text === 'Админ-панель' && {
                  color: 'warning.main',
                }),
              }}
            >
              {item.icon}
            </ListItemIcon>
            <ListItemText
              primary={item.text}
              primaryTypographyProps={{
                fontWeight: item.text === 'Админ-панель' ? 'bold' : 'normal',
              }}
            />
          </ListItem>
        ))}
      </List>

      {/* Данные вошедшего пользователя внизу меню */}
      {user && (
        <>
          <Divider sx={{ mt: 2 }} />
          <Box sx={{ p: 2 }}>
            {/* noWrap обрезает длинный email вместо переноса строки */}
            <Typography variant="body2" color="text.secondary" noWrap>
              {user.email || 'Пользователь'}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {user.first_name || ''} {user.last_name || ''}
            </Typography>
          </Box>
        </>
      )}
    </Box>
  );

  return (
    <Box
      component="nav"
      sx={{ width: { sm: 240 }, flexShrink: { sm: 0 } }}
    >
      {/* Вариант для телефонов: выдвигается поверх содержимого.
          display управляет тем, какой из двух Drawer показывать */}
      <Drawer
        variant="temporary"
        open={open}
        onClose={onClose}
        // keepMounted оставляет меню в разметке страницы —
        // открывается быстрее, лучше для мобильных устройств
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: 'block', sm: 'none' },   // только на узких экранах
          '& .MuiDrawer-paper': { boxSizing: 'border-box', width: 240 },
        }}
      >
        {drawer}
      </Drawer>

      {/* Вариант для компьютеров: видно всегда, закрыть нельзя */}
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: 'none', sm: 'block' },   // только на широких экранах
          '& .MuiDrawer-paper': { boxSizing: 'border-box', width: 240 },
        }}
        open
      >
        {drawer}
      </Drawer>
    </Box>
  );
};

export default Sidebar;
