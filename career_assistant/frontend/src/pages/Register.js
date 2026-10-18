import React, { useState } from 'react';
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Link,
  Alert,
  Grid,
} from '@mui/material';
import { useForm } from 'react-hook-form';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { PersonAdd as PersonAddIcon } from '@mui/icons-material';

const Register = () => {
  const { register: registerUser } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState('');
  
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm();

  const password = watch('password');

  const onSubmit = async (data) => {
    try {
      setError('');
      const result = await registerUser(data);
      if (result.success) {
        navigate('/');
      } else {
        setError(result.error || 'Ошибка регистрации');
      }
    } catch (err) {
      setError('Произошла ошибка при регистрации');
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        bgcolor: 'background.default',
        py: 4,
      }}
    >
      <Container maxWidth="md">
        <Paper
          elevation={3}
          sx={{
            p: 4,
            borderRadius: 2,
          }}
        >
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <PersonAddIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
            <Typography variant="h4" component="h1" gutterBottom>
              Регистрация в Career Assistant
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Создайте аккаунт для начала работы
            </Typography>
          </Box>

          {error && typeof error === 'string' && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit(onSubmit)}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
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

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Телефон"
                  {...register('phone')}
                  error={!!errors.phone}
                  helperText={errors.phone?.message}
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Имя"
                  {...register('first_name', {
                    required: 'Имя обязательно',
                  })}
                  error={!!errors.first_name}
                  helperText={errors.first_name?.message}
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Фамилия"
                  {...register('last_name', {
                    required: 'Фамилия обязательна',
                  })}
                  error={!!errors.last_name}
                  helperText={errors.last_name?.message}
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

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Пароль"
                  type="password"
                  {...register('password', {
                    required: 'Пароль обязателен',
                    minLength: {
                      value: 8,
                      message: 'Пароль должен содержать минимум 8 символов',
                    },
                  })}
                  error={!!errors.password}
                  helperText={errors.password?.message}
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Подтверждение пароля"
                  type="password"
                  {...register('password2', {
                    required: 'Подтверждение пароля обязательно',
                    validate: (value) =>
                      value === password || 'Пароли не совпадают',
                  })}
                  error={!!errors.password2}
                  helperText={errors.password2?.message}
                />
              </Grid>
            </Grid>

            <Button
              fullWidth
              type="submit"
              variant="contained"
              size="large"
              disabled={isSubmitting}
              sx={{ mt: 4, mb: 2 }}
            >
              {isSubmitting ? 'Регистрация...' : 'Зарегистрироваться'}
            </Button>

            <Box sx={{ textAlign: 'center', mt: 3 }}>
              <Typography variant="body2" color="text.secondary">
                Уже есть аккаунт?{' '}
                <Link component={RouterLink} to="/login" color="primary">
                  Войти
                </Link>
              </Typography>
            </Box>
          </form>
        </Paper>
      </Container>
    </Box>
  );
};

export default Register;