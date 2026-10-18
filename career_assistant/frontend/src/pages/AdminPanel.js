import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TextField,
  Button,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Card,
  CardContent,
  Switch,
  FormControlLabel,
  Tooltip,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  Edit as EditIcon,
  Block as BlockIcon,
  CheckCircle as CheckCircleIcon,
  Refresh as RefreshIcon,
  Person as PersonIcon,
  Description as DescriptionIcon,
  Work as WorkIcon,
  Send as SendIcon
} from '@mui/icons-material';
import { adminAPI } from '../api';
import { toast } from 'react-toastify';

const AdminPanel = () => {
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [search, setSearch] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editForm, setEditForm] = useState({});

  useEffect(() => {
    fetchData();
  }, [page, rowsPerPage, search]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Загружаем пользователей
      const params = {
        page: page + 1,
        limit: rowsPerPage,
        search: search
      };
      
      const usersResponse = await adminAPI.getUsers(params);
      setUsers(usersResponse.data || []);
      
      // Загружаем статистику
      const statsResponse = await adminAPI.getStats();
      setStats(statsResponse.data);
      
    } catch (error) {
      console.error('Error fetching admin data:', error);
      toast.error('Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleActive = async (userId) => {
    try {
      await adminAPI.toggleUserActive(userId);
      toast.success('Статус пользователя обновлен');
      fetchData();
    } catch (error) {
      toast.error('Ошибка обновления статуса');
    }
  };

  const handleEditUser = (user) => {
    setSelectedUser(user);
    setEditForm({
      first_name: user.first_name || '',
      last_name: user.last_name || '',
      phone: user.phone || '',
      specialization: user.specialization || ''
    });
    setEditDialogOpen(true);
  };

  const handleSaveEdit = async () => {
    try {
      await adminAPI.updateUser(selectedUser.id, editForm);
      toast.success('Данные пользователя обновлены');
      setEditDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error('Ошибка обновления данных');
    }
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Никогда';
    return new Date(dateString).toLocaleDateString('ru-RU');
  };

  if (loading && !users.length) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
        Панель администратора
      </Typography>

      {/* Статистика */}
      {stats && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <PersonIcon color="primary" sx={{ mr: 2, fontSize: 40 }} />
                  <Box>
                    <Typography variant="h4" component="div">
                      {stats.total_users}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Всего пользователей
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <CheckCircleIcon color="success" sx={{ mr: 2, fontSize: 40 }} />
                  <Box>
                    <Typography variant="h4" component="div">
                      {stats.active_users}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Активных
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <DescriptionIcon color="info" sx={{ mr: 2, fontSize: 40 }} />
                  <Box>
                    <Typography variant="h4" component="div">
                      {stats.total_resumes || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Резюме
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <SendIcon color="warning" sx={{ mr: 2, fontSize: 40 }} />
                  <Box>
                    <Typography variant="h4" component="div">
                      {stats.total_applications || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Заявок
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Панель управления */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            Управление пользователями
          </Typography>
          <Box display="flex" gap={2}>
            <TextField
              placeholder="Поиск по email, имени..."
              size="small"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              sx={{ width: 300 }}
            />
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={fetchData}
            >
              Обновить
            </Button>
          </Box>
        </Box>

        {/* Таблица пользователей */}
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>Имя</TableCell>
                <TableCell>Телефон</TableCell>
                <TableCell>Дата регистрации</TableCell>
                <TableCell>Последний вход</TableCell>
                <TableCell>Статус</TableCell>
                <TableCell>Роль</TableCell>
                <TableCell>Действия</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.id} hover>
                  <TableCell>{user.id}</TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                      {user.email}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {user.first_name} {user.last_name}
                  </TableCell>
                  <TableCell>{user.phone || 'Не указан'}</TableCell>
                  <TableCell>{formatDate(user.date_joined)}</TableCell>
                  <TableCell>{formatDate(user.last_login)}</TableCell>
                  <TableCell>
                    <Chip
                      label={user.is_active ? 'Активен' : 'Заблокирован'}
                      color={user.is_active ? 'success' : 'error'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={user.is_superuser ? 'Админ' : 'Пользователь'}
                      color={user.is_superuser ? 'warning' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Box display="flex" gap={1}>
                      <Tooltip title="Редактировать">
                        <IconButton
                          size="small"
                          onClick={() => handleEditUser(user)}
                          color="primary"
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title={user.is_active ? "Заблокировать" : "Активировать"}>
                        <IconButton
                          size="small"
                          onClick={() => handleToggleActive(user.id)}
                          color={user.is_active ? "error" : "success"}
                        >
                          <BlockIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <TablePagination
          rowsPerPageOptions={[5, 10, 25, 50]}
          component="div"
          count={users.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          labelRowsPerPage="Строк на странице:"
          labelDisplayedRows={({ from, to, count }) => `${from}-${to} из ${count}`}
        />
      </Paper>

      {/* Диалог редактирования пользователя */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Редактирование пользователя</DialogTitle>
        <DialogContent>
          {selectedUser && (
            <Box sx={{ pt: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Email: {selectedUser.email}
              </Typography>
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Имя"
                    value={editForm.first_name}
                    onChange={(e) => setEditForm({...editForm, first_name: e.target.value})}
                    margin="normal"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Фамилия"
                    value={editForm.last_name}
                    onChange={(e) => setEditForm({...editForm, last_name: e.target.value})}
                    margin="normal"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Телефон"
                    value={editForm.phone}
                    onChange={(e) => setEditForm({...editForm, phone: e.target.value})}
                    margin="normal"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Специализация"
                    value={editForm.specialization}
                    onChange={(e) => setEditForm({...editForm, specialization: e.target.value})}
                    margin="normal"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={selectedUser.is_active}
                        onChange={() => handleToggleActive(selectedUser.id)}
                        color="primary"
                      />
                    }
                    label="Активный пользователь"
                  />
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Отмена</Button>
          <Button onClick={handleSaveEdit} variant="contained" color="primary">
            Сохранить
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default AdminPanel;