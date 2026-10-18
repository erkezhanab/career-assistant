import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  Grid,
  Alert,
  Switch,
  FormControlLabel,
  Divider,
  Card,
  CardContent,
  CardActions,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Save as SaveIcon,
  Lock as LockIcon,
  Delete as DeleteIcon,
  Notifications as NotificationsIcon,
  Email as EmailIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';
import { useForm } from 'react-hook-form';
import { useAuth } from '../context/AuthContext';
import { authAPI } from '../api';
import { toast } from 'react-toastify';

const SettingsPage = () => {
  const { user, updateProfile } = useAuth();
  const [notifications, setNotifications] = useState({
    enabled: true,
    email: true,
    searchFrequency: 'daily',
  });
  const [deleteDialog, setDeleteDialog] = useState(false);
  const [passwordDialog, setPasswordDialog] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm({
    defaultValues: {
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      email: user?.email || '',
      phone: user?.phone || '',
      specialization: user?.specialization || '',
    },
  });

  useEffect(() => {
    if (user) {
      reset({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        phone: user.phone || '',
        specialization: user.specialization || '',
      });
    }
  }, [user, reset]);

  const onSubmit = async (data) => {
    try {
      await updateProfile(data);
      toast.success('Профиль обновлен');
    } catch (error) {
      toast.error('Ошибка обновления профиля');
    }
  };

  const handleChangePassword = async (data) => {
    try {
      await authAPI.changePassword(data);
      toast.success('Пароль изменен');
      setPasswordDialog(false);
    } catch (error) {
      toast.error('Ошибка изменения пароля');
    }
  };

  const handleDeleteAccount = async () => {
    try {
      // Здесь должен быть API вызов для удаления аккаунта
      toast.info('Функция удаления аккаунта в разработке');
      setDeleteDialog(false);
    } catch (error) {
      toast.error('Ошибка удаления аккаунта');
    }
  };

  return (
    <Container maxWidth="lg">
      <Typography variant="h4" gutterBottom>
        Настройки
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Управляйте настройками вашего аккаунта
      </Typography>

      <Grid container spacing={4}>
        {/* Основная информация */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Основная информация
            </Typography>
            <form onSubmit={handleSubmit(onSubmit)}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Имя"
                    {...register('first_name')}
                    error={!!errors.first_name}
                    helperText={errors.first_name?.message}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Фамилия"
                    {...register('last_name')}
                    error={!!errors.last_name}
                    helperText={errors.last_name?.message}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Email"
                    type="email"
                    {...register('email', {
                      required: 'Email обязателен',
                      pattern: {
                        value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                        message: 'Некорректный email адрес',
                      },
                    })}
                    error={!!errors.email}
                    helperText={errors.email?.message}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Телефон"
                    {...register('phone')}
                    error={!!errors.phone}
                    helperText={errors.phone?.message}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Специальность"
                    {...register('specialization')}
                    error={!!errors.specialization}
                    helperText={errors.specialization?.message}
                  />
                </Grid>
                <Grid item xs={12}>
                  <Button
                    type="submit"
                    variant="contained"
                    startIcon={<SaveIcon />}
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? 'Сохранение...' : 'Сохранить изменения'}
                  </Button>
                </Grid>
              </Grid>
            </form>
          </Paper>
        </Grid>

        {/* Настройки уведомлений */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <NotificationsIcon sx={{ mr: 1 }} />
              <Typography variant="h6">Уведомления</Typography>
            </Box>
            
            <FormControlLabel
              control={
                <Switch
                  checked={notifications.enabled}
                  onChange={(e) => setNotifications({...notifications, enabled: e.target.checked})}
                  color="primary"
                />
              }
              label="Включить уведомления"
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={notifications.email}
                  onChange={(e) => setNotifications({...notifications, email: e.target.checked})}
                  color="primary"
                  disabled={!notifications.enabled}
                />
              }
              label="Email уведомления"
              sx={{ ml: 0 }}
            />
            
            <FormControl fullWidth sx={{ mt: 2, mb: 2 }}>
              <InputLabel>Частота поиска вакансий</InputLabel>
              <Select
                value={notifications.searchFrequency}
                onChange={(e) => setNotifications({...notifications, searchFrequency: e.target.value})}
                label="Частота поиска вакансий"
                disabled={!notifications.enabled}
              >
                <MenuItem value="daily">Ежедневно</MenuItem>
                <MenuItem value="weekly">Еженедельно</MenuItem>
                <MenuItem value="monthly">Ежемесячно</MenuItem>
              </Select>
            </FormControl>
            
            <Button
              variant="outlined"
              onClick={() => {
                // Сохранение настроек уведомлений
                toast.success('Настройки уведомлений сохранены');
              }}
            >
              Сохранить настройки
            </Button>
          </Paper>

          {/* Безопасность */}
          <Paper sx={{ p: 3, mt: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <SecurityIcon sx={{ mr: 1 }} />
              <Typography variant="h6">Безопасность</Typography>
            </Box>
            
            <Button
              variant="outlined"
              startIcon={<LockIcon />}
              onClick={() => setPasswordDialog(true)}
              sx={{ mb: 2 }}
            >
              Изменить пароль
            </Button>
            
            <Divider sx={{ my: 2 }} />
            
            <Typography variant="body2" color="text.secondary" paragraph>
              Удаление аккаунта безвозвратно удалит все ваши данные, включая резюме и историю откликов.
            </Typography>
            
            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={() => setDeleteDialog(true)}
            >
              Удалить аккаунт
            </Button>
          </Paper>
        </Grid>
      </Grid>

      {/* Диалог изменения пароля */}
      <Dialog open={passwordDialog} onClose={() => setPasswordDialog(false)}>
        <DialogTitle>Изменение пароля</DialogTitle>
        <DialogContent>
          <form id="password-form" onSubmit={handleSubmit(handleChangePassword)}>
            <TextField
              fullWidth
              type="password"
              label="Текущий пароль"
              margin="normal"
              required
            />
            <TextField
              fullWidth
              type="password"
              label="Новый пароль"
              margin="normal"
              required
            />
            <TextField
              fullWidth
              type="password"
              label="Подтвердите новый пароль"
              margin="normal"
              required
            />
          </form>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPasswordDialog(false)}>Отмена</Button>
          <Button type="submit" form="password-form" variant="contained">
            Изменить пароль
          </Button>
        </DialogActions>
      </Dialog>

      {/* Диалог удаления аккаунта */}
      <Dialog open={deleteDialog} onClose={() => setDeleteDialog(false)}>
        <DialogTitle>Удаление аккаунта</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            Это действие необратимо. Все ваши данные будут удалены.
          </Alert>
          <Typography variant="body2">
            Для подтверждения удаления введите ваш пароль:
          </Typography>
          <TextField
            fullWidth
            type="password"
            label="Пароль"
            margin="normal"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog(false)}>Отмена</Button>
          <Button onClick={handleDeleteAccount} color="error" variant="contained">
            Удалить аккаунт
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default SettingsPage;