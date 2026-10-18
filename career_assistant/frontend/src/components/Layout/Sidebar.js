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
  const location = useLocation();
  const [user, setUser] = useState(null);
  const [isAdmin, setIsAdmin] = useState(false);
  
  useEffect(() => {
    loadUserInfo();
  }, []);
  
  const loadUserInfo = async () => {
    try {
      // Пробуем получить данные пользователя разными способами
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
        localStorage.setItem('user', JSON.stringify(userInfo));
      }
    } catch (error) {
      console.error('Error loading user info:', error);
      // Устанавливаем дефолтные значения
      setUser({ email: '', first_name: '', last_name: '' });
      setIsAdmin(false);
    }
  };
  
  const allMenuItems = isAdmin 
    ? [...menuItems, { text: 'Админ-панель', icon: <AdminPanelIcon />, path: '/admin' }]
    : menuItems;

  const drawer = (
    <Box sx={{ width: 240 }}>
      <Box sx={{ p: 3 }}>
        <Typography variant="h6" sx={{ fontWeight: 600, color: 'primary.main' }}>
          Career Assistant
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Ваш помощник в карьере
        </Typography>
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
        {allMenuItems.map((item) => (
          <ListItem
            button
            key={item.text}
            onClick={() => {
              navigate(item.path);
              onClose();
            }}
            sx={{
              bgcolor: location.pathname === item.path ? 'primary.light' : 'transparent',
              color: location.pathname === item.path ? 'primary.contrastText' : 'inherit',
              '&:hover': {
                bgcolor: 'primary.light',
                color: 'primary.contrastText',
              },
              borderRadius: 1,
              mx: 1,
              my: 0.5,
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
      
      {user && (
        <>
          <Divider sx={{ mt: 2 }} />
          <Box sx={{ p: 2 }}>
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
      <Drawer
        variant="temporary"
        open={open}
        onClose={onClose}
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: 'block', sm: 'none' },
          '& .MuiDrawer-paper': { boxSizing: 'border-box', width: 240 },
        }}
      >
        {drawer}
      </Drawer>
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: 'none', sm: 'block' },
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