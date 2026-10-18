// frontend/src/pages/ResumeUpload.jsx
import React, { useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  LinearProgress,
  Alert,
  Grid,
  Card,
  CardContent,
} from '@mui/material';
import { Upload as UploadIcon, Description as DescriptionIcon } from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import axios from '../api/axiosConfig';

const ResumeUpload = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [analysis, setAnalysis] = useState(null);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: 1,
    onDrop: (acceptedFiles) => {
      setFile(acceptedFiles[0]);
    },
  });

  const handleUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setUploading(true);

    try {
      const response = await axios.post('/resumes/upload/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setProgress(percentCompleted);
        },
      });

      // Запускаем опрос для получения результатов анализа
      pollAnalysis(response.data.id);
    } catch (error) {
      console.error('Upload failed:', error);
      setUploading(false);
    }
  };

  const pollAnalysis = async (resumeId) => {
    let attempts = 0;
    const maxAttempts = 30; // 30 попыток по 2 секунды = 60 секунд

    const interval = setInterval(async () => {
      attempts++;
      
      try {
        const response = await axios.get(`/resumes/${resumeId}/analysis/`);
        
        if (response.data.analyzed_at) {
          clearInterval(interval);
          setAnalysis(response.data);
          setUploading(false);
          setProgress(100);
        }
      } catch (error) {
        console.error('Polling error:', error);
      }

      if (attempts >= maxAttempts) {
        clearInterval(interval);
        setUploading(false);
      }
    }, 2000);
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4, mb: 6 }}>
        <Typography variant="h4" gutterBottom>
          Загрузка резюме
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Загрузите ваше резюме для анализа и получения рекомендаций
        </Typography>
      </Box>

      <Grid container spacing={4}>
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
              minHeight: 300,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              alignItems: 'center',
            }}
          >
            <input {...getInputProps()} />
            <UploadIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              {isDragActive
                ? 'Отпустите файл здесь'
                : 'Перетащите файл сюда или нажмите для выбора'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Поддерживаемые форматы: PDF, DOC, DOCX (максимум 10MB)
            </Typography>
            {file && (
              <Box sx={{ mt: 2 }}>
                <DescriptionIcon />
                <Typography variant="body2">{file.name}</Typography>
              </Box>
            )}
          </Paper>

          <Button
            fullWidth
            variant="contained"
            size="large"
            onClick={handleUpload}
            disabled={!file || uploading}
            sx={{ mt: 2 }}
          >
            {uploading ? 'Анализируем...' : 'Загрузить и проанализировать'}
          </Button>

          {uploading && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress variant="determinate" value={progress} />
              <Typography variant="body2" align="center" sx={{ mt: 1 }}>
                {progress}%
              </Typography>
            </Box>
          )}
        </Grid>

        <Grid item xs={12} md={6}>
          {analysis ? (
            <Card>
              <CardContent>
                <Typography variant="h5" gutterBottom>
                  Результаты анализа
                </Typography>
                
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Общая оценка
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={analysis.overall_score * 10} 
                    sx={{ height: 10, borderRadius: 5 }}
                  />
                  <Typography variant="h3" align="center" sx={{ mt: 1 }}>
                    {analysis.overall_score}/10
                  </Typography>
                </Box>

                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Alert severity="success" sx={{ mb: 2 }}>
                      <Typography variant="subtitle2">Сильные стороны</Typography>
                      <ul>
                        {analysis.strong_points?.split('\n').map((point, index) => (
                          <li key={index}>{point}</li>
                        ))}
                      </ul>
                    </Alert>
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <Alert severity="warning" sx={{ mb: 2 }}>
                      <Typography variant="subtitle2">Что улучшить</Typography>
                      <ul>
                        {analysis.improvements?.split('\n').map((point, index) => (
                          <li key={index}>{point}</li>
                        ))}
                      </ul>
                    </Alert>
                  </Grid>
                </Grid>

                <Alert severity="info" sx={{ mt: 2 }}>
                  <Typography variant="subtitle2">Рекомендации</Typography>
                  <Typography variant="body2">{analysis.recommendations}</Typography>
                </Alert>

                {analysis.status === 'approved' && (
                  <Alert severity="success" sx={{ mt: 2 }}>
                    Ваше резюме прошло проверку и готово к использованию!
                  </Alert>
                )}
              </CardContent>
            </Card>
          ) : (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <DescriptionIcon sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                Результаты анализа появятся здесь
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Загрузите резюме, чтобы получить оценку и рекомендации от ИИ
              </Typography>
            </Paper>
          )}
        </Grid>
      </Grid>
    </Container>
  );
};

export default ResumeUpload;