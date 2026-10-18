import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Avatar,
  Button,
  Card,
  CardContent,
  Chip,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  Alert,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import CardActions from '@mui/material/CardActions';
import {
  Edit as EditIcon,
  Download as DownloadIcon,
  Visibility as VisibilityIcon,
  CheckCircle,
  Pending,
  Block,
  Timeline as TimelineIcon,
  Description as DescriptionIcon,
  Work as WorkIcon,
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { resumesAPI, applicationsAPI } from '../api';
import { toast } from 'react-toastify';

const ProfilePage = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState(0);
  const [resumes, setResumes] = useState([]);
  const [applications, setApplications] = useState([]);
  const [stats, setStats] = useState({
    totalApplications: 0,
    pendingApplications: 0,
    viewedApplications: 0,
    invitedApplications: 0,
    rejectedApplications: 0,
  });
  const [analysisDialog, setAnalysisDialog] = useState(null);

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

      // Calculate stats
      const stats = {
        totalApplications: applicationsRes.data.length,
        pendingApplications: applicationsRes.data.filter(a => a.status === 'pending').length,
        viewedApplications: applicationsRes.data.filter(a => a.status === 'viewed').length,
        invitedApplications: applicationsRes.data.filter(a => a.status === 'invited').length,
        rejectedApplications: applicationsRes.data.filter(a => a.status === 'rejected').length,
      };
      setStats(stats);
    } catch (error) {
      toast.error('Ошибка загрузки данных');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'warning';
      case 'viewed': return 'info';
      case 'invited': return 'success';
      case 'rejected': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending': return <Pending />;
      case 'viewed': return <VisibilityIcon />;
      case 'invited': return <CheckCircle />;
      case 'rejected': return <Block />;
      default: return null;
    }
  };

  const handleViewAnalysis = async (resumeId) => {
    try {
      const response = await resumesAPI.getResumeAnalysis(resumeId);
      setAnalysisDialog(response.data);
    } catch (error) {
      toast.error('Ошибка загрузки анализа');
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <Container maxWidth="xl">
      {/* Заголовок профиля */}
      <Paper sx={{ p: 4, mb: 4 }}>
        <Grid container spacing={3} alignItems="center">
          <Grid item>
            <Avatar
              sx={{
                width: 100,
                height: 100,
                bgcolor: 'primary.main',
                fontSize: 36,
              }}
            >
              {user?.first_name?.[0]}{user?.last_name?.[0]}
            </Avatar>
          </Grid>
          <Grid item xs>
            <Typography variant="h4">
              {user?.first_name} {user?.last_name}
            </Typography>
            <Typography variant="body1" color="text.secondary" gutterBottom>
              {user?.specialization || 'Специальность не указана'}
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Typography variant="body2">
                <strong>Email:</strong> {user?.email}
              </Typography>
              {user?.phone && (
                <Typography variant="body2">
                  <strong>Телефон:</strong> {user.phone}
                </Typography>
              )}
            </Box>
          </Grid>
          <Grid item>
            <Button
              variant="outlined"
              startIcon={<EditIcon />}
              onClick={() => window.location.href = '/settings'}
            >
              Редактировать профиль
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Табы */}
      <Tabs 
        value={activeTab} 
        onChange={(e, newValue) => setActiveTab(newValue)}
        sx={{ mb: 3 }}
      >
        <Tab label="Обзор" icon={<TimelineIcon />} iconPosition="start" />
        <Tab label="Резюме" icon={<DescriptionIcon />} iconPosition="start" />
        <Tab label="Отклики" icon={<WorkIcon />} iconPosition="start" />
      </Tabs>

      {/* Контент табов */}
      {activeTab === 0 && (
        <Grid container spacing={3}>
          {/* Статистика */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Статистика откликов
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Card sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="primary">
                      {stats.totalApplications}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Всего откликов
                    </Typography>
                  </Card>
                </Grid>
                <Grid item xs={6}>
                  <Card sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="success">
                      {stats.invitedApplications}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Приглашений
                    </Typography>
                  </Card>
                </Grid>
                <Grid item xs={6}>
                  <Card sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="warning">
                      {stats.pendingApplications}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      На рассмотрении
                    </Typography>
                  </Card>
                </Grid>
                <Grid item xs={6}>
                  <Card sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="error">
                      {stats.rejectedApplications}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Отклонено
                    </Typography>
                  </Card>
                </Grid>
              </Grid>
            </Paper>
          </Grid>

          {/* Активные резюме */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Активные резюме
              </Typography>
              {resumes.length === 0 ? (
                <Alert severity="info">У вас нет активных резюме</Alert>
              ) : (
                resumes.slice(0, 3).map((resume) => (
                  <Card key={resume.id} sx={{ mb: 2 }}>
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="subtitle1">
                          {resume.original_filename}
                        </Typography>
                        <Chip 
                          label={resume.status} 
                          color={resume.status === 'approved' ? 'success' : 'warning'}
                          size="small"
                        />
                      </Box>
                      {resume.overall_score && (
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="body2" color="text.secondary">
                            Оценка: {resume.overall_score}/10
                          </Typography>
                          <LinearProgress 
                            variant="determinate" 
                            value={resume.overall_score * 10}
                            sx={{ height: 6, borderRadius: 3 }}
                          />
                        </Box>
                      )}
                    </CardContent>
                  </Card>
                ))
              )}
            </Paper>
          </Grid>
        </Grid>
      )}

      {activeTab === 1 && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6">Мои резюме</Typography>
            <Button
              variant="contained"
              onClick={() => window.location.href = '/resumes'}
            >
              Загрузить новое резюме
            </Button>
          </Box>
          
          {resumes.length === 0 ? (
            <Alert severity="info">
              У вас еще нет загруженных резюме. Загрузите первое резюме для анализа.
            </Alert>
          ) : (
            <Grid container spacing={3}>
              {resumes.map((resume) => (
                <Grid item xs={12} md={6} key={resume.id}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {getStatusIcon(resume.status)}
                          <Typography variant="h6">
                            {resume.original_filename}
                          </Typography>
                        </Box>
                        <Chip 
                          label={resume.status} 
                          color={getStatusColor(resume.status)}
                          size="small"
                        />
                      </Box>
                      
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Загружено: {formatDate(resume.upload_date)}
                      </Typography>
                      
                      {resume.overall_score && (
                        <Box sx={{ mt: 2, mb: 2 }}>
                          <Typography variant="body2" gutterBottom>
                            Оценка ИИ: {resume.overall_score}/10
                          </Typography>
                          <LinearProgress 
                            variant="determinate" 
                            value={resume.overall_score * 10}
                            color={resume.overall_score >= 7 ? 'success' : resume.overall_score >= 5 ? 'warning' : 'error'}
                            sx={{ height: 8, borderRadius: 4 }}
                          />
                        </Box>
                      )}
                      
                      {resume.analyzed_at && (
                        <Typography variant="caption" color="text.secondary">
                          Проанализировано: {formatDate(resume.analyzed_at)}
                        </Typography>
                      )}
                    </CardContent>
                    
                    <CardActions>
                      <Button
                        size="small"
                        startIcon={<VisibilityIcon />}
                        onClick={() => handleViewAnalysis(resume.id)}
                        disabled={resume.status === 'pending'}
                      >
                        Анализ
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </Paper>
      )}

      {activeTab === 2 && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6">История откликов</Typography>
            <Typography variant="body2" color="text.secondary">
              Всего: {applications.length}
            </Typography>
          </Box>
          
          {applications.length === 0 ? (
            <Alert severity="info">
              У вас еще нет отправленных откликов.
            </Alert>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Вакансия</TableCell>
                    <TableCell>Компания</TableCell>
                    <TableCell>Дата отклика</TableCell>
                    <TableCell>Статус</TableCell>
                    <TableCell>Сопроводительное письмо</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {applications.map((application) => (
                    <TableRow key={application.id}>
                      <TableCell>
                        <Typography variant="body2">
                          {application.vacancy_name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {application.company_name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatDate(application.applied_at)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={application.status}
                          color={getStatusColor(application.status)}
                          size="small"
                          icon={getStatusIcon(application.status)}
                        />
                      </TableCell>
                      <TableCell>
                        <Button
                          size="small"
                          onClick={() => {
                            navigator.clipboard.writeText(application.cover_letter);
                            toast.success('Письмо скопировано в буфер обмена');
                          }}
                        >
                          Копировать
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Paper>
      )}

      {/* Диалог анализа */}
      <Dialog
        open={!!analysisDialog}
        onClose={() => setAnalysisDialog(null)}
        maxWidth="md"
        fullWidth
      >
        {analysisDialog && (
          <>
            <DialogTitle>Анализ резюме</DialogTitle>
            <DialogContent dividers>
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Общая оценка: {analysisDialog.overall_score}/10
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={analysisDialog.overall_score * 10}
                  sx={{ height: 10, borderRadius: 5 }}
                />
              </Box>

              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Alert severity="success" sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Сильные стороны
                    </Typography>
                    <ul>
                      {analysisDialog.strong_points?.split('\n').map((point, index) => (
                        <li key={index}>
                          <Typography variant="body2">{point}</Typography>
                        </li>
                      ))}
                    </ul>
                  </Alert>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Alert severity="warning" sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Что улучшить
                    </Typography>
                    <ul>
                      {analysisDialog.improvements?.split('\n').map((point, index) => (
                        <li key={index}>
                          <Typography variant="body2">{point}</Typography>
                        </li>
                      ))}
                    </ul>
                  </Alert>
                </Grid>
              </Grid>

              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Рекомендации
                </Typography>
                <Typography variant="body2">
                  {analysisDialog.recommendations}
                </Typography>
              </Alert>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setAnalysisDialog(null)}>Закрыть</Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Container>
  );
};

export default ProfilePage;