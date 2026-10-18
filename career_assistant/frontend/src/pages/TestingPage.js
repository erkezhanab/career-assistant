import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Tabs,
  Tab,
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Alert,
  CircularProgress,
  LinearProgress,
  Chip,
  Radio,
  RadioGroup,
  FormControlLabel,
  Checkbox,
  FormGroup,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stepper,
  Step,
  StepLabel,
  Avatar,
  Fade,
  Zoom
} from '@mui/material';
import {
  Add,
  Delete,
  Assignment,
  CloudUpload,
  Quiz,
  Timer,
  EmojiEvents,
  CheckCircle,
  Cancel,
  Description,
  School,
  Close,
  AutoAwesome,
  HourglassEmpty,
  Psychology,
  Description as DescriptionIcon,
  CheckCircleOutline,
  Visibility,
  Download,
  ZoomIn,
  ZoomOut,
  Fullscreen,
  FullscreenExit,
  ArrowBack,
  ArrowForward
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { testingService } from '../api/testingAPI';
import { toast } from 'react-toastify';

const TestingPage = () => {
  const [tab, setTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [documents, setDocuments] = useState([]);
  const [testStatus, setTestStatus] = useState(null);
  const [userResumes, setUserResumes] = useState([]);
  const [selectedResume, setSelectedResume] = useState(null);
  
  // Состояния для управления тестированием
  const [testPhase, setTestPhase] = useState('selection'); // 'selection', 'generating', 'testing', 'results'
  const [generationProgress, setGenerationProgress] = useState(0);
  const [currentSession, setCurrentSession] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [testProgress, setTestProgress] = useState({ current: 0, total: 0 });
  const [userAnswers, setUserAnswers] = useState({});
  const [testResults, setTestResults] = useState(null);
  
  // Диалоги
  const [documentDialogOpen, setDocumentDialogOpen] = useState(false);
  const [newDocument, setNewDocument] = useState({
    title: '',
    issuer: '',
    document_type: 'certificate',
    issue_date: new Date().toISOString().split('T')[0],
    file: null
  });

  const [activeStep, setActiveStep] = useState(0);

  // Состояния для просмотра сертификатов
  const [viewerOpen, setViewerOpen] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [zoom, setZoom] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [statusRes, docsRes, resumesRes] = await Promise.allSettled([
        testingService.getTestStatus(),
        testingService.getCertificates(),
        testingService.getAvailableResumes ? testingService.getAvailableResumes() : Promise.resolve({data: []})
      ]);

      if (statusRes.status === 'fulfilled') {
        setTestStatus(statusRes.value.data);
        
        // Проверяем активный тест
        if (statusRes.value.data.has_active_test && statusRes.value.data.active_session) {
          const session = statusRes.value.data.active_session;
          
          if (session.status === 'generating') {
            setTestPhase('generating');
            setCurrentSession(session);
            checkGenerationStatus(session.id);
          } else if (session.status === 'in_progress') {
            setTestPhase('testing');
            setCurrentSession(session);
            loadCurrentQuestion(session.id);
          }
        }
      }

      if (docsRes.status === 'fulfilled') {
        setDocuments(docsRes.value.data);
      }

      if (resumesRes.status === 'fulfilled') {
        setUserResumes(resumesRes.value.data);
        if (resumesRes.value.data.length > 0 && !selectedResume) {
          setSelectedResume(resumesRes.value.data[0]);
        }
      }
    } catch (error) {
      console.error('Ошибка загрузки данных:', error);
      toast.error('Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  // Проверка статуса генерации вопросов
  const checkGenerationStatus = async (sessionId) => {
    try {
      const response = await testingService.getSessionStatus(sessionId);
      
      if (response.data.questions_ready) {
        // Вопросы готовы!
        setTestPhase('testing');
        setCurrentSession(response.data);
        loadCurrentQuestion(sessionId);
        setActiveStep(2);
        toast.success('Вопросы сгенерированы! Тест начинается...');
      } else {
        // Продолжаем ждать
        setGenerationProgress(prev => Math.min(prev + 10, 90));
        setTimeout(() => checkGenerationStatus(sessionId), 2000);
      }
    } catch (error) {
      console.error('Ошибка проверки статуса:', error);
    }
  };

  const loadCurrentQuestion = async (sessionId) => {
    try {
      const response = await testingService.getQuestion(sessionId);
      
      if (response.data.completed) {
        // Тест завершен
        completeTest();
      } else {
        setCurrentQuestion({
          ...response.data.question,
          userAnswer: ''
        });
        setTestProgress(response.data.progress);
      }
    } catch (error) {
      console.error('Ошибка загрузки вопроса:', error);
    }
  };

  const startTest = async () => {
    if (!selectedResume) {
      toast.error('Выберите резюме для генерации вопросов');
      return;
    }
    
    try {
      setTestPhase('generating');
      setGenerationProgress(0);
      setActiveStep(1);
      
      const response = await testingService.startTest({
        resume_id: selectedResume.id,
        question_count: 10
      });
      
      if (response.data.error) {
        toast.error(response.data.error);
        setTestPhase('selection');
        setActiveStep(0);
        return;
      }
      
      if (response.data.generating) {
        // Запускаем анимацию генерации
        setCurrentSession(response.data);
        
        // Начинаем проверку статуса
        setTimeout(() => checkGenerationStatus(response.data.id), 3000);
        
        toast.info('ИИ анализирует ваше резюме и генерирует вопросы...');
      } else {
        // Вопросы уже готовы
        setTestPhase('testing');
        setCurrentSession(response.data);
        setActiveStep(2);
        loadCurrentQuestion(response.data.id);
      }
      
    } catch (error) {
      console.error('Ошибка начала теста:', error);
      toast.error(error.response?.data?.error || 'Ошибка начала теста');
      setTestPhase('selection');
      setActiveStep(0);
    }
  };

  const submitAnswer = async (answer) => {
    if (!currentSession || !currentQuestion) {
      toast.error('Нет активного вопроса');
      return;
    }
    
    try {
      // Подготавливаем ответ для отправки
      let answerToSend = answer;
      
      // Если это multiple choice и ответ - массив
      if (currentQuestion.question_type === 'multiple_choice' && Array.isArray(answer)) {
        answerToSend = answer;
      } 
      // Если это single choice и пользователь выбрал вариант
      else if (currentQuestion.question_type === 'single_choice' && answer) {
        answerToSend = answer;
      }
      // Если это открытый вопрос
      else if (currentQuestion.question_type === 'open_ended' && typeof answer === 'string') {
        answerToSend = answer.trim();
      } else {
        answerToSend = answer || '';
      }
      
      const response = await testingService.submitAnswer(
        currentSession.id,
        currentQuestion.id,
        answerToSend
      );
      
      // Сохраняем ответ локально
      setUserAnswers(prev => ({
        ...prev,
        [currentQuestion.id]: answerToSend
      }));
      
      // Ждем немного перед загрузкой следующего вопроса
      setTimeout(async () => {
        await loadCurrentQuestion(currentSession.id);
      }, 500);
      
    } catch (error) {
      console.error('Ошибка отправки ответа:', error);
      
      let errorMessage = 'Ошибка отправки ответа';
      
      if (error.response?.data?.error) {
        errorMessage = error.response.data.error;
      }
      
      toast.error(errorMessage);
    }
  };

  const completeTest = async () => {
    if (!currentSession) return;
    
    try {
      const response = await testingService.completeTest(currentSession.id);
      setTestResults(response.data);
      setTestPhase('results');
      setActiveStep(3);
      
      // Обновляем статус
      await loadAllData();
      
      toast.success(response.data.passed ? 
        'Поздравляем! Тест пройден!' : 
        'Тест завершен. Попробуйте еще раз через 7 дней.');
        
    } catch (error) {
      console.error('Ошибка завершения теста:', error);
      toast.error('Ошибка завершения теста');
    }
  };

  const resetTest = () => {
    setTestPhase('selection');
    setActiveStep(0);
    setTestResults(null);
    setCurrentQuestion(null);
    setCurrentSession(null);
    setTestProgress({ current: 0, total: 0 });
    setUserAnswers({});
  };

  // Drag & Drop для документов
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg'],
      'application/pdf': ['.pdf']
    },
    maxSize: 10 * 1024 * 1024,
    onDrop: (acceptedFiles, rejectedFiles) => {
      if (rejectedFiles.length > 0) {
        toast.error('Неподдерживаемый формат файла или слишком большой размер');
        return;
      }
      
      if (acceptedFiles.length > 0) {
        setNewDocument(prev => ({
          ...prev,
          file: acceptedFiles[0]
        }));
      }
    }
  });

  const uploadDocument = async () => {
    if (!newDocument.title || !newDocument.issuer || !newDocument.file) {
      toast.error('Заполните все обязательные поля');
      return;
    }
    
    try {
      const formData = new FormData();
      formData.append('title', newDocument.title);
      formData.append('issuer', newDocument.issuer);
      formData.append('document_type', newDocument.document_type);
      formData.append('issue_date', newDocument.issue_date);
      formData.append('document_file', newDocument.file);
      
      await testingService.addCertificate(formData);
      
      toast.success('Документ успешно загружен');
      setDocumentDialogOpen(false);
      setNewDocument({
        title: '',
        issuer: '',
        document_type: 'certificate',
        issue_date: new Date().toISOString().split('T')[0],
        file: null
      });
      
      // Обновляем список
      await loadAllData();
      
    } catch (error) {
      console.error('Ошибка загрузки документа:', error);
      toast.error('Ошибка загрузки документа');
    }
  };

  const deleteDocument = async (id) => {
    if (!window.confirm('Удалить документ?')) return;
    
    try {
      await testingService.deleteCertificate(id);
      toast.success('Документ удален');
      await loadAllData();
    } catch (error) {
      console.error('Ошибка удаления:', error);
      toast.error('Ошибка удаления документа');
    }
  };

  // Функции для просмотра сертификатов
  const handleViewDocument = (doc) => {
    setSelectedDocument(doc);
    setZoom(1);
    setViewerOpen(true);
  };

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev + 0.25, 3));
  };

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev - 0.25, 0.5));
  };

  const handleDownload = () => {
    if (!selectedDocument?.file_url) {
      toast.error('Ссылка на файл недоступна');
      return;
    }
    
    const link = document.createElement('a');
    link.href = selectedDocument.file_url;
    link.download = `${selectedDocument.title}.${selectedDocument.file_url.split('.').pop()}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const toggleFullscreen = () => {
    const elem = document.querySelector('.certificate-content');
    
    if (!isFullscreen) {
      if (elem.requestFullscreen) {
        elem.requestFullscreen();
      } else if (elem.webkitRequestFullscreen) {
        elem.webkitRequestFullscreen();
      }
      setIsFullscreen(true);
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
      }
      setIsFullscreen(false);
    }
  };

  // Обработчик выхода из полноэкранного режима
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);

  // Компонент анимации генерации
  const GenerationAnimation = () => (
    <Fade in={true} timeout={1000}>
      <Box sx={{ 
        textAlign: 'center', 
        py: 8,
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        borderRadius: 2,
        color: 'white'
      }}>
        <AutoAwesome sx={{ fontSize: 80, mb: 3, animation: 'pulse 2s infinite' }} />
        
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold' }}>
          Генерация персонализированных вопросов
        </Typography>
        
        <Typography variant="body1" sx={{ mb: 4, maxWidth: 600, mx: 'auto' }}>
          Искусственный интеллект анализирует ваше резюме и создает уникальные вопросы, 
          соответствующие вашему опыту и навыкам
        </Typography>
        
        <Box sx={{ maxWidth: 400, mx: 'auto', mb: 4 }}>
          <LinearProgress 
            variant="determinate" 
            value={generationProgress}
            sx={{ 
              height: 10, 
              borderRadius: 5,
              backgroundColor: 'rgba(255,255,255,0.3)',
              '& .MuiLinearProgress-bar': {
                backgroundColor: 'white'
              }
            }}
          />
          <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
            Прогресс: {generationProgress}%
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, flexWrap: 'wrap' }}>
          <Chip 
            icon={<Psychology />} 
            label="Анализ резюме" 
            sx={{ background: 'rgba(255,255,255,0.2)', color: 'white' }}
          />
          <Chip 
            icon={<AutoAwesome />} 
            label="Генерация вопросов" 
            sx={{ background: 'rgba(255,255,255,0.2)', color: 'white' }}
          />
          <Chip 
            icon={<HourglassEmpty />} 
            label="Оптимизация сложности" 
            sx={{ background: 'rgba(255,255,255,0.2)', color: 'white' }}
          />
        </Box>
      </Box>
    </Fade>
  );

  // Компонент выбора резюме
  const ResumeSelection = () => (
    <Zoom in={true}>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <DescriptionIcon />
            Выберите резюме для тестирования
          </Typography>
          
          <Typography variant="body2" color="text.secondary" paragraph>
            ИИ проанализирует выбранное резюме и сгенерирует персонализированные вопросы
          </Typography>
          
          {userResumes.length === 0 ? (
            <Alert severity="warning">
              У вас нет загруженных резюме. Загрузите резюме в разделе "Мои резюме" сначала.
            </Alert>
          ) : (
            <Grid container spacing={2}>
              {userResumes.map((resume) => (
                <Grid item xs={12} md={6} key={resume.id}>
                  <Card
                    variant={selectedResume?.id === resume.id ? "outlined" : "outlined"}
                    sx={{
                      cursor: 'pointer',
                      borderColor: selectedResume?.id === resume.id ? 'primary.main' : 'transparent',
                      borderWidth: 2,
                      '&:hover': {
                        borderColor: 'primary.light',
                        backgroundColor: 'action.hover'
                      }
                    }}
                    onClick={() => setSelectedResume(resume)}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                        <Avatar sx={{ bgcolor: selectedResume?.id === resume.id ? 'primary.main' : 'grey.300' }}>
                          <DescriptionIcon />
                        </Avatar>
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="subtitle1" fontWeight="bold">
                            {resume.title}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Загружено: {new Date(resume.upload_date).toLocaleDateString()}
                          </Typography>
                        </Box>
                        {selectedResume?.id === resume.id && (
                          <CheckCircleOutline color="primary" />
                        )}
                      </Box>
                      
                      {resume.overall_score && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          <LinearProgress 
                            variant="determinate" 
                            value={resume.overall_score * 10}
                            sx={{ flex: 1, height: 6 }}
                          />
                          <Typography variant="caption">
                            {resume.overall_score}/10
                          </Typography>
                        </Box>
                      )}
                      
                      <Typography variant="body2" color="text.secondary" noWrap>
                        {resume.preview}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
          
          {userResumes.length > 0 && (
            <Box sx={{ mt: 3, textAlign: 'center' }}>
              <Button
                variant="contained"
                size="large"
                onClick={startTest}
                disabled={!selectedResume}
                startIcon={<AutoAwesome />}
              >
                Сгенерировать вопросы на основе выбранного резюме
              </Button>
              
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Процесс займет 30-60 секунд
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>
    </Zoom>
  );

  // Компонент вопроса
  const renderQuestion = () => {
    if (!currentQuestion) return null;
    
    const handleAnswerSubmit = () => {
      if (!currentQuestion) {
        toast.error('Нет активного вопроса');
        return;
      }
      
      let userAnswer;
      
      if (currentQuestion.question_type === 'single_choice') {
        userAnswer = currentQuestion.userAnswer;
        if (!userAnswer) {
          toast.error('Выберите вариант ответа');
          return;
        }
      } 
      else if (currentQuestion.question_type === 'multiple_choice') {
        userAnswer = currentQuestion.userAnswer || [];
        if (userAnswer.length === 0) {
          toast.error('Выберите хотя бы один вариант');
          return;
        }
      }
      else if (currentQuestion.question_type === 'open_ended') {
        userAnswer = currentQuestion.userAnswer || '';
        if (!userAnswer.trim()) {
          toast.error('Введите ответ');
          return;
        }
      }
      
      submitAnswer(userAnswer);
    };
    
    return (
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6">
              Вопрос {testProgress.current} из {testProgress.total}
            </Typography>
            <Chip 
              icon={<Timer />} 
              label={`Время: 90 сек`}
              color="primary"
              variant="outlined"
            />
          </Box>
          
          <LinearProgress 
            variant="determinate" 
            value={(testProgress.current / testProgress.total) * 100}
            sx={{ mb: 3, height: 8 }}
          />
          
          <Typography variant="body1" paragraph sx={{ 
            fontSize: '1.1rem', 
            fontWeight: 500,
            mb: 3 
          }}>
            {currentQuestion.question_text}
          </Typography>
          
          {currentQuestion.question_type === 'single_choice' && (
            <RadioGroup
              value={currentQuestion.userAnswer || ''}
              onChange={(e) => setCurrentQuestion({
                ...currentQuestion,
                userAnswer: e.target.value
              })}
            >
              {currentQuestion.options.map((option, index) => (
                <FormControlLabel
                  key={index}
                  value={option}
                  control={<Radio />}
                  label={option}
                  sx={{ 
                    mb: 1,
                    border: '1px solid #eee',
                    borderRadius: 1,
                    p: 1,
                    '&:hover': { bgcolor: 'action.hover' }
                  }}
                />
              ))}
            </RadioGroup>
          )}
          
          {currentQuestion.question_type === 'multiple_choice' && (
            <FormGroup>
              {currentQuestion.options.map((option, index) => (
                <FormControlLabel
                  key={index}
                  control={
                    <Checkbox
                      checked={(currentQuestion.userAnswer || []).includes(option)}
                      onChange={(e) => {
                        const currentAnswers = currentQuestion.userAnswer || [];
                        if (e.target.checked) {
                          setCurrentQuestion({
                            ...currentQuestion,
                            userAnswer: [...currentAnswers, option]
                          });
                        } else {
                          setCurrentQuestion({
                            ...currentQuestion,
                            userAnswer: currentAnswers.filter(a => a !== option)
                          });
                        }
                      }}
                    />
                  }
                  label={option}
                  sx={{ 
                    mb: 1,
                    border: '1px solid #eee',
                    borderRadius: 1,
                    p: 1,
                    '&:hover': { bgcolor: 'action.hover' }
                  }}
                />
              ))}
            </FormGroup>
          )}
          
          {currentQuestion.question_type === 'open_ended' && (
            <TextField
              fullWidth
              multiline
              rows={4}
              value={currentQuestion.userAnswer || ''}
              onChange={(e) => setCurrentQuestion({
                ...currentQuestion,
                userAnswer: e.target.value
              })}
              placeholder="Введите ваш ответ..."
              sx={{ mb: 2 }}
            />
          )}
          
          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
            <Button
              variant="contained"
              onClick={handleAnswerSubmit}
              disabled={
                (!currentQuestion.userAnswer || 
                (Array.isArray(currentQuestion.userAnswer) && currentQuestion.userAnswer.length === 0))
              }
            >
              {testProgress.current === testProgress.total ? 'Завершить тест' : 'Ответить и продолжить'}
            </Button>
            
            <Typography variant="body2" color="text.secondary">
              Вопрос {testProgress.current} из {testProgress.total}
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  };

  // Компонент результатов
  const renderResults = () => {
    if (!testResults) return null;
    
    return (
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Box sx={{ textAlign: 'center', mb: 3 }}>
            {testResults.passed ? (
              <>
                <CheckCircle sx={{ fontSize: 80, color: 'success.main', mb: 2 }} />
                <Typography variant="h4" color="success.main" gutterBottom>
                  Поздравляем!
                </Typography>
                <Typography variant="h6" gutterBottom>
                  Вы успешно прошли тест
                </Typography>
              </>
            ) : (
              <>
                <Cancel sx={{ fontSize: 80, color: 'error.main', mb: 2 }} />
                <Typography variant="h4" color="error.main" gutterBottom>
                  Тест не пройден
                </Typography>
                <Typography variant="h6" gutterBottom>
                  Попробуйте снова через 7 дней
                </Typography>
              </>
            )}
          </Box>
          
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={6}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h3" color="primary">
                  {testResults.score}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Результат
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={6}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h3" color="primary">
                  {testResults.correct_count}/{testResults.total_questions}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Правильных ответов
                </Typography>
              </Paper>
            </Grid>
          </Grid>
          
          <Button
            variant="contained"
            fullWidth
            onClick={resetTest}
          >
            Вернуться к тестированию
          </Button>
        </CardContent>
      </Card>
    );
  };

  const renderTestingTabContent = () => {
    if (testPhase === 'generating') {
      return <GenerationAnimation />;
    } else if (testPhase === 'testing') {
      return renderQuestion();
    } else if (testPhase === 'results') {
      return renderResults();
    } else {
      return (
        <>
          {activeStep === 0 && <ResumeSelection />}
          
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="subtitle1" gutterBottom>
              Тестирование Frontend Developer
            </Typography>
            <Typography variant="body2">
              • 10 профессиональных вопросов, сгенерированных на основе вашего резюме
              <br />
              • Время: ~20 минут
              <br />
              • Проходной балл: 70%
              <br />
              • Вопросы по: React, JavaScript, TypeScript, CSS, Web технологиям
            </Typography>
          </Alert>

          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Paper sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Quiz sx={{ mr: 2, color: 'primary.main' }} />
                  <Typography variant="h6">
                    Готовы подтвердить свои навыки?
                  </Typography>
                </Box>
                
                <Typography variant="body2" color="text.secondary" paragraph>
                  Вопросы будут сгенерированы искусственным интеллектом на основе 
                  анализа вашего резюме и будут соответствовать вашему уровню опыта.
                </Typography>
                
                <Box sx={{ mt: 3 }}>
                  {testStatus?.last_score !== null && testStatus?.last_score !== undefined && (
                    <Alert 
                      severity={testStatus.last_score >= 70 ? "success" : "warning"}
                      sx={{ mb: 2 }}
                    >
                      Последний результат: {testStatus.last_score}% 
                      ({testStatus.last_score >= 70 ? 'пройден' : 'не пройден'})
                    </Alert>
                  )}
                  
                  {testStatus?.next_retake_date && (
                    <Alert severity="warning" sx={{ mb: 2 }}>
                      Следующая попытка доступна с: {' '}
                      {new Date(testStatus.next_retake_date).toLocaleDateString()}
                    </Alert>
                  )}
                  
                  {userResumes.length > 0 && selectedResume ? (
                    <Button
                      variant="contained"
                      size="large"
                      fullWidth
                      onClick={startTest}
                      disabled={!testStatus?.can_start_new_test}
                      startIcon={<EmojiEvents />}
                    >
                      {testStatus?.has_active_test ? 'Продолжить тест' : 'Начать тестирование'}
                    </Button>
                  ) : (
                    <Alert severity="warning">
                      Загрузите резюме в разделе "Мои резюме" для начала тестирования
                    </Alert>
                  )}
                </Box>
              </Paper>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 3, textAlign: 'center' }}>
                <Description sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Используется ваше резюме
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Вопросы генерируются на основе анализа вашего загруженного резюме
                </Typography>
                <Chip 
                  label={`Загружено документов: ${documents.length}`}
                  color="primary"
                  variant="outlined"
                />
              </Paper>
            </Grid>
          </Grid>
        </>
      );
    }
  };

  // Рендеринг контента документа
  const renderDocumentContent = () => {
    if (!selectedDocument?.file_url) {
      return (
        <Box sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          justifyContent: 'center',
          height: '100%',
          p: 3
        }}>
          <DescriptionIcon sx={{ fontSize: 80, color: 'grey.400', mb: 3 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            Файл документа недоступен
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Ссылка на файл отсутствует или недоступна
          </Typography>
        </Box>
      );
    }

    const fileExtension = selectedDocument.file_url.split('.').pop()?.toLowerCase();

    if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(fileExtension)) {
      return (
        <Box sx={{ 
          width: '100%', 
          height: '100%', 
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'auto',
          bgcolor: 'grey.100'
        }}>
          <img
            src={selectedDocument.file_url}
            alt={selectedDocument.title}
            style={{
              maxWidth: '100%',
              maxHeight: '100%',
              transform: `scale(${zoom})`,
              transition: 'transform 0.3s ease',
              objectFit: 'contain'
            }}
          />
        </Box>
      );
    } else if (fileExtension === 'pdf') {
      return (
        <Box sx={{ 
          width: '100%', 
          height: '100%',
          overflow: 'auto',
          bgcolor: 'grey.100'
        }}>
          <iframe
            src={selectedDocument.file_url}
            title={selectedDocument.title}
            style={{
              width: '100%',
              height: '100%',
              border: 'none'
            }}
          />
        </Box>
      );
    } else {
      return (
        <Box sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          justifyContent: 'center',
          height: '100%',
          p: 3
        }}>
          <DescriptionIcon sx={{ fontSize: 80, color: 'grey.400', mb: 3 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            Формат файла не поддерживается для просмотра
          </Typography>
          <Button
            variant="outlined"
            startIcon={<Download />}
            onClick={handleDownload}
            sx={{ mt: 2 }}
          >
            Скачать файл
          </Button>
        </Box>
      );
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 6 }}>
      <Paper sx={{ p: 4 }}>
        {/* Заголовок */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <Assignment sx={{ fontSize: 40, mr: 2, color: 'primary.main' }} />
          <Box>
            <Typography variant="h4" gutterBottom>
              Профессиональная верификация
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Подтвердите свои знания и квалификацию для повышения доверия работодателей
            </Typography>
          </Box>
        </Box>

        {/* Степпер */}
        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          <Step>
            <StepLabel>Выбор резюме</StepLabel>
          </Step>
          <Step>
            <StepLabel>Генерация вопросов</StepLabel>
          </Step>
          <Step>
            <StepLabel>Прохождение теста</StepLabel>
          </Step>
          <Step>
            <StepLabel>Результаты</StepLabel>
          </Step>
        </Stepper>

        {/* Основной контент */}
        {testPhase === 'generating' || testPhase === 'testing' || testPhase === 'results' ? (
          renderTestingTabContent()
        ) : (
          <>
            {/* Вкладки */}
            <Tabs 
              value={tab} 
              onChange={(e, newValue) => setTab(newValue)} 
              sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}
            >
              <Tab 
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Quiz />
                    Тестирование
                  </Box>
                } 
              />
              <Tab 
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Description />
                    Документы
                  </Box>
                } 
              />
            </Tabs>

            {/* Содержимое вкладок */}
            {tab === 0 ? (
              // Вкладка тестирования
              <Box>
                {renderTestingTabContent()}
              </Box>
            ) : (
              // Вкладка документов
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                  <Typography variant="h6">
                    Загруженные документы
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<CloudUpload />}
                    onClick={() => setDocumentDialogOpen(true)}
                  >
                    Загрузить документ
                  </Button>
                </Box>

                {/* Drag & Drop зона */}
                <Paper
                  {...getRootProps()}
                  sx={{
                    p: 4,
                    mb: 3,
                    border: '2px dashed',
                    borderColor: isDragActive ? 'primary.main' : 'grey.300',
                    bgcolor: isDragActive ? 'action.hover' : 'background.paper',
                    textAlign: 'center',
                    cursor: 'pointer',
                    minHeight: 150,
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    alignItems: 'center'
                  }}
                >
                  <input {...getInputProps()} />
                  <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    {isDragActive ? 'Отпустите файлы здесь' : 'Перетащите файлы сюда'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    или нажмите для выбора файлов (PDF, JPG, PNG до 10MB)
                  </Typography>
                </Paper>

                {/* Список документов */}
                {documents.length === 0 ? (
                  <Alert severity="info">
                    Документы не загружены. Загрузите дипломы, сертификаты или курсы.
                  </Alert>
                ) : (
                  <Grid container spacing={2}>
                    {documents.map((doc) => (
                      <Grid item xs={12} md={6} key={doc.id}>
                        <Card>
                          <CardContent>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                              <Box sx={{ flex: 1, cursor: 'pointer' }} onClick={() => handleViewDocument(doc)}>
                                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                  {doc.document_type === 'diploma' ? (
                                    <School sx={{ mr: 1, color: 'primary.main' }} />
                                  ) : doc.document_type === 'course' ? (
                                    <Assignment sx={{ mr: 1, color: 'secondary.main' }} />
                                  ) : (
                                    <Description sx={{ mr: 1, color: 'success.main' }} />
                                  )}
                                  <Typography variant="subtitle1" fontWeight="bold">
                                    {doc.title}
                                  </Typography>
                                </Box>
                                
                                <Typography variant="body2" color="text.secondary" gutterBottom>
                                  {doc.issuer}
                                </Typography>
                                
                                <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                                  <Chip
                                    label={doc.document_type === 'diploma' ? 'Диплом' : 
                                           doc.document_type === 'course' ? 'Курс' : 'Сертификат'}
                                    size="small"
                                    color="primary"
                                    variant="outlined"
                                  />
                                  
                                  {doc.is_verified && (
                                    <Chip
                                      icon={<CheckCircle />}
                                      label="Проверен"
                                      size="small"
                                      color="success"
                                      variant="outlined"
                                    />
                                  )}
                                </Box>
                                
                                <Typography variant="caption" color="text.secondary">
                                  Выдан: {new Date(doc.issue_date).toLocaleDateString()}
                                  {doc.expiry_date && ` • Действует до: ${new Date(doc.expiry_date).toLocaleDateString()}`}
                                </Typography>
                              </Box>
                              
                              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                                <IconButton
                                  size="small"
                                  color="primary"
                                  onClick={() => handleViewDocument(doc)}
                                  title="Просмотреть"
                                >
                                  <Visibility />
                                </IconButton>
                                
                                <IconButton
                                  size="small"
                                  color="error"
                                  onClick={() => deleteDocument(doc.id)}
                                  title="Удалить"
                                >
                                  <Delete />
                                </IconButton>
                              </Box>
                            </Box>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                )}
              </Box>
            )}
          </>
        )}
      </Paper>

      {/* Диалог загрузки документа */}
      <Dialog 
        open={documentDialogOpen} 
        onClose={() => setDocumentDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Загрузка документа
          <IconButton
            aria-label="close"
            onClick={() => setDocumentDialogOpen(false)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <Close />
          </IconButton>
        </DialogTitle>
        
        <DialogContent dividers>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Тип документа</InputLabel>
              <Select
                value={newDocument.document_type}
                label="Тип документа"
                onChange={(e) => setNewDocument({...newDocument, document_type: e.target.value})}
              >
                <MenuItem value="diploma">Диплом</MenuItem>
                <MenuItem value="certificate">Сертификат</MenuItem>
                <MenuItem value="course">Курс</MenuItem>
              </Select>
            </FormControl>

            <TextField
              label="Название документа"
              fullWidth
              required
              value={newDocument.title}
              onChange={(e) => setNewDocument({...newDocument, title: e.target.value})}
              placeholder="Например: Сертификат React Developer"
            />

            <TextField
              label="Организация"
              fullWidth
              required
              value={newDocument.issuer}
              onChange={(e) => setNewDocument({...newDocument, issuer: e.target.value})}
              placeholder="Например: Яндекс.Практикум"
            />

            <TextField
              label="Дата выдачи"
              type="date"
              fullWidth
              required
              InputLabelProps={{ shrink: true }}
              value={newDocument.issue_date}
              onChange={(e) => setNewDocument({...newDocument, issue_date: e.target.value})}
            />

            {/* Поле загрузки файла */}
            <Box sx={{ border: '1px dashed #ccc', p: 3, borderRadius: 1, textAlign: 'center' }}>
              {newDocument.file ? (
                <Box>
                  <Description sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
                  <Typography variant="body1" gutterBottom>
                    {newDocument.file.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {(newDocument.file.size / (1024 * 1024)).toFixed(2)} MB
                  </Typography>
                  <Button
                    size="small"
                    sx={{ mt: 1 }}
                    onClick={() => setNewDocument({...newDocument, file: null})}
                  >
                    Изменить файл
                  </Button>
                </Box>
              ) : (
                <Box {...getRootProps()}>
                  <input {...getInputProps()} />
                  <CloudUpload sx={{ fontSize: 40, color: 'primary.main', mb: 2 }} />
                  <Typography variant="body1" gutterBottom>
                    Нажмите или перетащите файл
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Поддерживаемые форматы: PDF, JPG, PNG (до 10MB)
                  </Typography>
                </Box>
              )}
            </Box>
          </Box>
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setDocumentDialogOpen(false)}>
            Отмена
          </Button>
          <Button
            variant="contained"
            onClick={uploadDocument}
            disabled={!newDocument.title || !newDocument.issuer || !newDocument.file}
          >
            Загрузить
          </Button>
        </DialogActions>
      </Dialog>

      {/* Диалог просмотра сертификата */}
      <Dialog 
        open={viewerOpen} 
        onClose={() => setViewerOpen(false)}
        maxWidth="lg"
        fullWidth
        sx={{
          '& .MuiDialog-paper': {
            height: '80vh'
          }
        }}
      >
        <DialogTitle sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          pr: 2
        }}>
          <Box sx={{ maxWidth: 'calc(100% - 100px)' }}>
            <Typography variant="h6" noWrap>
              {selectedDocument?.title}
            </Typography>
            <Typography variant="body2" color="text.secondary" noWrap>
              {selectedDocument?.issuer} • {selectedDocument?.issue_date && new Date(selectedDocument.issue_date).toLocaleDateString()}
            </Typography>
          </Box>
          <IconButton onClick={() => setViewerOpen(false)}>
            <Close />
          </IconButton>
        </DialogTitle>
        
        <DialogContent dividers sx={{ p: 0, overflow: 'hidden' }}>
          <Box className="certificate-content" sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* Панель управления */}
            <Box sx={{ 
              p: 1, 
              bgcolor: 'grey.50', 
              borderBottom: 1, 
              borderColor: 'divider',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: 1
            }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <IconButton
                  size="small"
                  onClick={handleZoomOut}
                  disabled={zoom <= 0.5}
                >
                  <ZoomOut />
                </IconButton>
                
                <Typography variant="body2" sx={{ minWidth: '80px' }}>
                  Масштаб: {Math.round(zoom * 100)}%
                </Typography>
                
                <IconButton
                  size="small"
                  onClick={handleZoomIn}
                  disabled={zoom >= 3}
                >
                  <ZoomIn />
                </IconButton>
                
                <Button
                  size="small"
                  variant="outlined"
                  onClick={() => setZoom(1)}
                  sx={{ ml: 1 }}
                >
                  100%
                </Button>
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <IconButton
                  size="small"
                  onClick={toggleFullscreen}
                  title={isFullscreen ? 'Выйти из полноэкранного режима' : 'Полноэкранный режим'}
                >
                  {isFullscreen ? <FullscreenExit /> : <Fullscreen />}
                </IconButton>
                
                <Button
                  size="small"
                  variant="contained"
                  startIcon={<Download />}
                  onClick={handleDownload}
                  disabled={!selectedDocument?.file_url}
                >
                  Скачать
                </Button>
              </Box>
            </Box>
            
            {/* Контент документа */}
            <Box sx={{ flex: 1, position: 'relative', overflow: 'auto' }}>
              {renderDocumentContent()}
            </Box>
          </Box>
        </DialogContent>
      </Dialog>
    </Container>
  );
};

export default TestingPage;