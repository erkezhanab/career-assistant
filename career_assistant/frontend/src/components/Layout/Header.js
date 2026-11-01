// Шапка сайта: название приложения и меню пользователя.
//
// Закреплена сверху (position="fixed") и видна на всех внутренних
// страницах. Содержит кнопку открытия бокового меню на телефонах
// и выпадающее меню профиля с выходом из системы.

import React from 'react';
import {
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  Box,
  Avatar,
  Menu,
  MenuItem,
  Tooltip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Notifications as NotificationsIcon,
  AccountCircle,
} from '@mui/icons-material';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';  // Импортируем useNavigate

// toggleSidebar приходит из Layout — открывает боковое меню
const Header = ({ toggleSidebar }) => {
  const { user, logout } = useAuth();

  // anchorEl хранит элемент, рядом с которым показать меню.
  // null = меню закрыто
  const [anchorEl, setAnchorEl] = React.useState(null);

  const navigate = useNavigate();  // Инициализируем navigate

  // Открытие меню: запоминаем кнопку, по которой щёлкнули,
  // чтобы меню появилось точно под ней
  const handleMenu = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    // Сначала закрываем меню, затем выходим —
    // иначе меню останется висеть при перезагрузке страницы
    handleClose();
    logout();
  };

  // Функция для перехода на страницу профиля
  const goToProfile = () => {
    navigate('/profile');  // Переход на профиль
    handleClose();
  };

  // Переход в настройки
  const goToSettings = () => {
    navigate('/settings');
    handleClose();
  };

  return (
    <AppBar
      position="fixed"
      sx={{
        // Шапка сдвинута вправо на ширину бокового меню,
        // чтобы не перекрывать его
        width: { sm: `calc(100% - 240px)` },
        ml: { sm: '240px' },
        bgcolor: 'background.paper',
        color: 'text.primary',
        boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
      }}
    >
      <Toolbar>
        {/* Кнопка-гамбургер. display: none на экранах от sm и выше —
            на компьютере боковое меню видно всегда, кнопка не нужна */}
        <IconButton
          color="inherit"
          aria-label="open drawer"
          edge="start"
          onClick={toggleSidebar}
          sx={{ mr: 2, display: { sm: 'none' } }}
        >
          <MenuIcon />
        </IconButton>

        {/* flexGrow: 1 растягивает название и прижимает
            остальные элементы к правому краю */}
        <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
          Career Assistant
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <IconButton color="inherit">
            <NotificationsIcon />
          </IconButton>

          <Tooltip title="Профиль">
            <IconButton
              onClick={handleMenu}
              size="small"
              sx={{ ml: 2 }}
              // aria-атрибуты нужны для программ чтения экрана:
              // они сообщают, что кнопка открывает меню
              aria-controls={anchorEl ? 'profile-menu' : undefined}
              aria-haspopup="true"
              aria-expanded={anchorEl ? 'true' : undefined}
            >
              <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
                {/* Первая буква имени, а если имени нет — общий значок.
                    ?. защищает от ошибки, пока данные ещё не загрузились */}
                {user?.first_name?.[0] || <AccountCircle />}
              </Avatar>
            </IconButton>
          </Tooltip>

          <Menu
            id="profile-menu"
            anchorEl={anchorEl}
            // Boolean() превращает элемент/null в true/false
            open={Boolean(anchorEl)}
            onClose={handleClose}
          >
            <MenuItem onClick={goToProfile}>Профиль</MenuItem>
            <MenuItem onClick={goToSettings}>Настройки</MenuItem>
            <MenuItem onClick={handleLogout}>Выйти</MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
