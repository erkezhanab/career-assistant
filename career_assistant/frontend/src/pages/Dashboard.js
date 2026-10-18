import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Button,
  Card,
  CardContent,
  CardActions,
  LinearProgress,
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Description as DescriptionIcon,
  Work as WorkIcon,
  Forum as ForumIcon,
  TrendingUp as TrendingUpIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { resumesAPI, applicationsAPI } from '../api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [resumes, setResumes] = useState([]);
  const [applications, setApplications] = useState([]);
  const [stats, setStats] = useState({
    totalResumes: 0,
    approvedResumes: 0,
    totalApplications: 0,
    pendingApplications: 0,
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [resumesRes, applicationsRes] = await Promise.all([
        resumesAPI.getUserResumes(),
        applicationsAPI.getUserApplications(),
      ]);

      setResumes(resumesRes.data);
      setApplications(applicationsRes.data);

      const approvedResumes = resumesRes.data.filter(r => r.status === 'approved').length;
      const pendingApplications = applicationsRes.data.filter(a => a.status === 'pending').length;

      setStats({
        totalResumes: resumesRes.data.length,
        approvedResumes,
        totalApplications: applicationsRes.data.length,
        pendingApplications,
      });
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  const getApplicationStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'warning';
      case 'viewed': return 'info';
      case 'invited': return 'success';
      case 'rejected': return 'error';
      default: return 'default';
    }
  };

  const getResumeStatusIcon = (status) => {
    switch (status) {
      case 'approved': return <CheckCircleIcon color="success" />;
      case 'rejected': return <WarningIcon color="error" />;
      default: return <ScheduleIcon color="warning" />;
    }
  };

  const chartData = [
    { name: 'Резюме', value: stats.totalResumes },
    { name: 'Одобрено', value: stats.approvedResumes },
    { name: 'Отклики', value: stats.totalApplications },
    { name: 'На рассмотрении', value: stats.pendingApplications },
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Добро пожаловать, {user?.first_name}!
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Ваш личный помощник в поиске работы и развитии карьеры
      </Typography>

      {/* Быстрые действия */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Button
            fullWidth
            variant="contained"
            startIcon={<DescriptionIcon />}
            onClick={() => navigate('/resumes')}
            sx={{ height: 80 }}
          >
            Загрузить резюме
          </Button>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Button
            fullWidth
            variant="outlined"
            startIcon={<WorkIcon />}
            onClick={() => navigate('/vacancies')}
            sx={{ height: 80 }}
          >
            Найти вакансии
          </Button>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Button
            fullWidth
            variant="outlined"
            startIcon={<ForumIcon />}
            onClick={() => navigate('/interviews')}
            sx={{ height: 80 }}
          >
            Подготовиться к собесу
          </Button>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Button
            fullWidth
            variant="outlined"
            startIcon={<TrendingUpIcon />}
            onClick={() => navigate('/profile')}
            sx={{ height: 80 }}
          >
            Статистика
          </Button>
        </Grid>
      </Grid>

      {/* Статистика */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Статистика
            </Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#2563eb" />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Общая информация
            </Typography>
            <List>
              <ListItem>
                <ListItemIcon>
                  <DescriptionIcon color="primary" />
                </ListItemIcon>
                <ListItemText 
                  primary="Резюме" 
                  secondary={`${stats.approvedResumes}/${stats.totalResumes} одобрено`}
                />
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemIcon>
                  <WorkIcon color="primary" />
                </ListItemIcon>
                <ListItemText 
                  primary="Отклики" 
                  secondary={`${stats.totalApplications} всего, ${stats.pendingApplications} на рассмотрении`}
                />
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemIcon>
                  <TrendingUpIcon color="primary" />
                </ListItemIcon>
                <ListItemText 
                  primary="Рейтинг резюме" 
                  secondary={
                    resumes.length > 0 
                      ? `Средний балл: ${(resumes.reduce((acc, r) => acc + (r.overall_score || 0), 0) / resumes.length).toFixed(1)}/10`
                      : 'Нет данных'
                  }
                />
              </ListItem>
            </List>
          </Paper>
        </Grid>

        {/* Последние резюме */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Последние резюме</Typography>
              <Button size="small" onClick={() => navigate('/resumes')}>
                Все резюме
              </Button>
            </Box>
            <List>
              {resumes.slice(0, 3).map((resume) => (
                <Card key={resume.id} sx={{ mb: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      {getResumeStatusIcon(resume.status)}
                      <Typography variant="subtitle1" sx={{ ml: 1 }}>
                        {resume.original_filename}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2" color="text.secondary">
                        {new Date(resume.upload_date).toLocaleDateString()}
                      </Typography>
                      {resume.overall_score && (
                        <Chip 
                          label={`${resume.overall_score}/10`} 
                          color={resume.overall_score >= 7 ? 'success' : resume.overall_score >= 5 ? 'warning' : 'error'}
                          size="small"
                        />
                      )}
                    </Box>
                  </CardContent>
                </Card>
              ))}
              {resumes.length === 0 && (
                <Typography color="text.secondary" align="center" py={3}>
                  Резюме еще не загружены
                </Typography>
              )}
            </List>
          </Paper>
        </Grid>

        {/* Последние отклики */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Последние отклики</Typography>
              <Button size="small" onClick={() => navigate('/profile')}>
                Все отклики
              </Button>
            </Box>
            <List>
              {applications.slice(0, 3).map((application) => (
                <Card key={application.id} sx={{ mb: 2 }}>
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom>
                      {application.vacancy_name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {application.company_name}
                    </Typography>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Chip 
                        label={application.status} 
                        color={getApplicationStatusColor(application.status)}
                        size="small"
                      />
                      <Typography variant="caption" color="text.secondary">
                        {new Date(application.applied_at).toLocaleDateString()}
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              ))}
              {applications.length === 0 && (
                <Typography color="text.secondary" align="center" py={3}>
                  Откликов еще нет
                </Typography>
              )}
            </List>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;