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
} from '@mui/material';
import { useForm } from 'react-hook-form';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Login as LoginIcon } from '@mui/icons-material';

const Login = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState('');
  
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm();

  const onSubmit = async (data) => {
    try {
      setError('');
      const result = await login(data.email, data.password);
      if (result.success) {
        navigate('/');
      } else {
        setError(result.error || 'Ошибка входа');
      }
    } catch (err) {
      setError('Произошла ошибка при входе');
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
      <Container maxWidth="sm">
        <Paper
          elevation={3}
          sx={{
            p: 4,
            borderRadius: 2,
          }}
        >
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <LoginIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
            <Typography variant="h4" component="h1" gutterBottom>
              Вход в Career Assistant
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Войдите в свой аккаунт для продолжения
            </Typography>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit(onSubmit)}>
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
              sx={{ mb: 3 }}
            />

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
              sx={{ mb: 3 }}
            />

            <Button
              fullWidth
              type="submit"
              variant="contained"
              size="large"
              disabled={isSubmitting}
              sx={{ mb: 2 }}
            >
              {isSubmitting ? 'Вход...' : 'Войти'}
            </Button>

            <Box sx={{ textAlign: 'center', mt: 3 }}>
              <Typography variant="body2" color="text.secondary">
                Нет аккаунта?{' '}
                <Link component={RouterLink} to="/register" color="primary">
                  Зарегистрироваться
                </Link>
              </Typography>
            </Box>
          </form>
        </Paper>
      </Container>
    </Box>
  );
};

export default Login;