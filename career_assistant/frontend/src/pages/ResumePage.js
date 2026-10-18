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
  Alert,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Delete as DeleteIcon,
  Visibility as VisibilityIcon,
  Download as DownloadIcon,
  CheckCircle,
  Warning,
  Schedule,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { resumesAPI } from '../api';
import { toast } from 'react-toastify';

const ResumePage = () => {
  const [resumes, setResumes] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [selectedFile, setSelectedFile] = useState(null);
  const [analysisDialog, setAnalysisDialog] = useState(null);

  useEffect(() => {
    fetchResumes();
  }, []);

  const fetchResumes = async () => {
    try {
      const response = await resumesAPI.getUserResumes();
      setResumes(response.data);
    } catch (error) {
      toast.error('Ошибка при загрузке резюме');
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: 1,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setSelectedFile(acceptedFiles[0]);
      }
    },
  });

  const handleUpload = async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);

    setUploading(true);
    setProgress(0);

    try {
      await resumesAPI.uploadResume(formData);
      toast.success('Резюме успешно загружено');
      setSelectedFile(null);
      fetchResumes();
    } catch (error) {
      toast.error('Ошибка при загрузке резюме');
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Вы уверены, что хотите удалить это резюме?')) {
      try {
        await resumesAPI.deleteResume(id);
        toast.success('Резюме удалено');
        fetchResumes();
      } catch (error) {
        toast.error('Ошибка при удалении резюме');
      }
    }
  };

  const handleViewAnalysis = async (id) => {
    try {
      const response = await resumesAPI.getResumeAnalysis(id);
      setAnalysisDialog(response.data);
    } catch (error) {
      toast.error('Ошибка при загрузке анализа');
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'approved': return <CheckCircle color="success" />;
      case 'rejected': return <Warning color="error" />;
      default: return <Schedule color="warning" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved': return 'success';
      case 'rejected': return 'error';
      default: return 'warning';
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Мои резюме
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Загрузите ваше резюме для анализа и получения рекомендаций от ИИ
      </Typography>

      {/* Загрузка резюме */}
      <Paper sx={{ p: 4, mb: 4 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper
              {...getRootProps()}
              sx={{
                p: 4,
                border: '2px dashed',
                borderColor: isDragActive ? 'primary.main' : 'grey.300',
                backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
                textAlign: 'center',
                cursor: 'pointer',
                minHeight: 200,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
              }}
            >
              <input {...getInputProps()} />
              <UploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                {isDragActive
                  ? 'Отпустите файл здесь'
                  : 'Перетащите файл сюда или нажмите для выбора'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Поддерживаемые форматы: PDF, DOC, DOCX (максимум 10MB)
              </Typography>
              {selectedFile && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2">{selectedFile.name}</Typography>
                </Box>
              )}
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <Typography variant="h6" gutterBottom>
                Требования к резюме
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Для лучшего анализа убедитесь, что ваше резюме содержит:
              </Typography>
              <ul>
                <li><Typography variant="body2">Контактную информацию</Typography></li>
                <li><Typography variant="body2">Опыт работы с датами</Typography></li>
                <li><Typography variant="body2">Образование</Typography></li>
                <li><Typography variant="body2">Навыки и технологии</Typography></li>
                <li><Typography variant="body2">Достижения и проекты</Typography></li>
              </ul>
              
              <Box sx={{ mt: 'auto' }}>
                <Button
                  fullWidth
                  variant="contained"
                  size="large"
                  onClick={handleUpload}
                  disabled={!selectedFile || uploading}
                  startIcon={<UploadIcon />}
                >
                  {uploading ? 'Загрузка...' : 'Загрузить резюме'}
                </Button>
                
                {uploading && (
                  <Box sx={{ mt: 2 }}>
                    <LinearProgress variant="determinate" value={progress} />
                  </Box>
                )}
              </Box>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Список резюме */}
      <Typography variant="h5" gutterBottom>
        Загруженные резюме
      </Typography>
      
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
                    Загружено: {new Date(resume.upload_date).toLocaleDateString()}
                  </Typography>
                  
                  {resume.overall_score && (
                    <Box sx={{ mt: 2 }}>
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
                      Проанализировано: {new Date(resume.analyzed_at).toLocaleDateString()}
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
                    Посмотреть анализ
                  </Button>
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => handleDelete(resume.id)}
                  >
                    <DeleteIcon />
                  </IconButton>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
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
    </Box>
  );
};

export default ResumePage;