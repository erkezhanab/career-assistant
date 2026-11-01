// Корневой компонент приложения.
//
// Решает две задачи:
//   1. подключает глобальные обёртки (тему оформления, контекст
//      авторизации, систему всплывающих уведомлений);
//   2. описывает маршрутизацию — какой компонент показывать
//      по какому адресу в браузере.

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import AdminPanel from './pages/AdminPanel';
import { AuthProvider } from './context/AuthContext';
import theme from './styles/theme';
import ProtectedRoute from './components/Common/ProtectedRoute';
import AdminRoute from './components/Common/AdminRoute';
import Layout from './components/Layout/Layout';

// Страницы
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import ResumePage from './pages/ResumePage';
import VacanciesPage from './pages/VacanciesPage';
import InterviewPage from './pages/InterviewPage';
import ProfilePage from './pages/ProfilePage';
import SettingsPage from './pages/SettingsPage';
import TestingPage from './pages/TestingPage';


function App() {
  return (
    // ThemeProvider задаёт единые цвета и шрифты для всех
    // компонентов Material UI (настройки в styles/theme.js)
    <ThemeProvider theme={theme}>
      {/* CssBaseline сбрасывает стандартные стили браузера,
          чтобы приложение одинаково выглядело в Chrome, Safari и Firefox */}
      <CssBaseline />

      {/* AuthProvider оборачивает всё приложение: данные пользователя
          доступны на любой странице через хук useAuth() */}
      <AuthProvider>
        <Router>
          <Routes>
            {/* Открытые страницы — доступны без входа в систему */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Защищённый раздел. ProtectedRoute проверяет наличие входа
                и перенаправляет на /login, если пользователь не авторизован.
                Layout рисует общий каркас: шапку и боковое меню */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              {/* Вложенные маршруты: отображаются внутри Layout
                  на месте компонента <Outlet />.
                  index — страница по умолчанию для адреса "/" */}
              <Route index element={<Dashboard />} />
              <Route path="resumes" element={<ResumePage />} />
              <Route path="vacancies" element={<VacanciesPage />} />
              <Route path="interviews" element={<InterviewPage />} />
              <Route path="testing" element={<TestingPage />} />
              <Route path="profile" element={<ProfilePage />} />
              <Route path="settings" element={<SettingsPage />} />
              {/* Админ-панель дополнительно закрыта AdminRoute:
                  обычный пользователь увидит сообщение об отказе */}
              <Route
                path="admin"
                element={
                  <AdminRoute>
                    <AdminPanel />
                  </AdminRoute>
                }
              />
            </Route>

            {/* "*" — любой несуществующий адрес.
                Вместо ошибки 404 пользователя возвращает на главную */}
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </Router>

        {/* Контейнер всплывающих уведомлений. Размещён один раз здесь,
            а вызывать уведомления можно из любого компонента
            через toast.success(...) / toast.error(...) */}
        <ToastContainer
          position="top-right"
          autoClose={3000}        // уведомление скрывается через 3 секунды
          hideProgressBar={false}
          newestOnTop={false}
          closeOnClick
          rtl={false}
          pauseOnFocusLoss
          draggable
          pauseOnHover            // таймер останавливается при наведении
        />
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
