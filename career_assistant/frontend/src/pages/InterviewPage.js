import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Button,
  Card,
  CardContent,
  CardActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Alert,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  Divider,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
  Rating,
  Avatar,
  ListItemAvatar,
  ListItemIcon,
  Collapse,
  IconButton,
  Backdrop,
  Fade,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Psychology as PsychologyIcon,
  QuestionAnswer as QuestionAnswerIcon,
  Lightbulb as LightbulbIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  ThumbUp as ThumbUpIcon,
  TipsAndUpdates as TipsAndUpdatesIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  ExpandLess as ExpandLessIcon,
  Warning as WarningIcon,
  Done as DoneIcon,
  Close as CloseIcon,
  AutoAwesome as AutoAwesomeIcon,
} from '@mui/icons-material';
import { interviewsAPI, resumesAPI } from '../api';
import { toast } from 'react-toastify';
import LoadingAnimation from '../components/LoadingAnimation';
import { CircularProgress } from '@mui/material';

const InterviewPage = () => {
  const [resumes, setResumes] = useState([]);
  const [selectedResume, setSelectedResume] = useState('');
  const [interviewType, setInterviewType] = useState('hr');
  const [generating, setGenerating] = useState(false);
  const [generatingFeedback, setGeneratingFeedback] = useState(false);
  const [currentInterview, setCurrentInterview] = useState(null);
  const [userAnswers, setUserAnswers] = useState({});
  const [completedInterviews, setCompletedInterviews] = useState([]);
  const [feedbackDialog, setFeedbackDialog] = useState(false);
  const [currentFeedback, setCurrentFeedback] = useState(null);
  const [loadingFeedback, setLoadingFeedback] = useState(false);
  const [expandedSections, setExpandedSections] = useState({});
  const [activeFeedbackTab, setActiveFeedbackTab] = useState(0);
  const [showAnalysisLoading, setShowAnalysisLoading] = useState(false);

  const interviewTypes = [
    { value: 'hr', label: 'HR интервью' },
    { value: 'technical', label: 'Техническое собеседование' },
    { value: 'stress', label: 'Стресс-интервью' },
    { value: 'behavioral', label: 'Поведенческое собеседование' },
  ];

  useEffect(() => {
    fetchResumes();
    fetchInterviews();
  }, []);

  const fetchResumes = async () => {
    try {
      const response = await resumesAPI.getUserResumes();
      const approvedResumes = response.data.filter(r => r.status === 'approved');
      setResumes(approvedResumes);
      if (approvedResumes.length > 0) {
        setSelectedResume(approvedResumes[0].id);
      }
    } catch (error) {
      toast.error('Ошибка загрузки резюме');
    }
  };

  const fetchInterviews = async () => {
    try {
      const response = await interviewsAPI.getUserInterviews();
      setCompletedInterviews(response.data);
    } catch (error) {
      console.error('Error fetching interviews:', error);
    }
  };

  const generateInterview = async () => {
    if (!selectedResume) {
      toast.error('Выберите резюме');
      return;
    }

    setGenerating(true);
    try {
      const response = await interviewsAPI.generateInterview({
        interview_type: interviewType,
        resume_id: selectedResume,
      });
      setCurrentInterview(response.data);
      setUserAnswers({});
      toast.success('Вопросы сгенерированы!');
    } catch (error) {
      toast.error('Ошибка генерации вопросов');
    } finally {
      setGenerating(false);
    }
  };

  const handleAnswerChange = (questionIndex, answer) => {
    setUserAnswers({
      ...userAnswers,
      [questionIndex]: answer,
    });
  };

  const completeInterview = async () => {
    if (!currentInterview) return;

    try {
      const answersArray = Object.keys(userAnswers).map(key => userAnswers[key]);
      
      // Показываем анимацию загрузки анализа
      setGeneratingFeedback(true);
      setShowAnalysisLoading(true);

      const response = await interviewsAPI.completeInterview(
        currentInterview.id,
        answersArray
      );

      // Имитируем загрузку для лучшего UX (минимум 1.5 секунды)
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Обновляем интервью с фидбеком
      const updatedInterview = {
        ...currentInterview,
        ...response.data.interview,
        userAnswers: answersArray,
        completedAt: new Date().toISOString(),
      };

      setCompletedInterviews([updatedInterview, ...completedInterviews]);
      setCurrentInterview(null);
      setUserAnswers({});
      
      // Показываем фидбек
      setCurrentFeedback(response.data.feedback);
      setGeneratingFeedback(false);
      setShowAnalysisLoading(false);
      setFeedbackDialog(true);
      
      toast.success('Анализ собеседования готов!');
    } catch (error) {
      setGeneratingFeedback(false);
      setShowAnalysisLoading(false);
      toast.error('Ошибка завершения собеседования');
    }
  };

  const loadFeedback = async (interviewId) => {
    setLoadingFeedback(true);
    setShowAnalysisLoading(true);
    try {
      // Имитируем загрузку для лучшего UX
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const response = await interviewsAPI.getInterviewFeedback(interviewId);
      setCurrentFeedback(response.data.feedback);
      setShowAnalysisLoading(false);
      setFeedbackDialog(true);
    } catch (error) {
      setShowAnalysisLoading(false);
      toast.error('Ошибка загрузки фидбека');
    } finally {
      setLoadingFeedback(false);
    }
  };

  const getInterviewStats = () => {
    if (!currentInterview?.questions) return null;
    
    const totalQuestions = currentInterview.questions.length;
    const answeredQuestions = Object.keys(userAnswers).length;
    const progress = (answeredQuestions / totalQuestions) * 100;

    return {
      totalQuestions,
      answeredQuestions,
      progress,
    };
  };

  const toggleSection = (section) => {
    setExpandedSections({
      ...expandedSections,
      [section]: !expandedSections[section]
    });
  };

  const renderFeedbackDialog = () => {
    if (!currentFeedback) return null;

    return (
      <Dialog 
        open={feedbackDialog} 
        onClose={() => setFeedbackDialog(false)}
        maxWidth="md"
        fullWidth
        TransitionComponent={Fade}
        TransitionProps={{ timeout: 500 }}
      >
        <DialogTitle>
          <Box display="flex" alignItems="center">
            <AutoAwesomeIcon sx={{ mr: 2, color: 'primary.main' }} />
            <Typography variant="h6">Анализ вашего собеседования</Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 4 }}>
            <Box display="flex" alignItems="center" sx={{ mb: 2 }}>
              <Rating
                value={currentFeedback.overall_score / 2}
                precision={0.5}
                readOnly
                size="large"
                icon={<StarIcon sx={{ color: '#FFD700' }} />}
                emptyIcon={<StarBorderIcon />}
              />
              <Typography variant="h5" sx={{ ml: 2 }}>
                {currentFeedback.overall_score.toFixed(1)}/10
              </Typography>
            </Box>
            <Typography variant="body1" color="text.secondary">
              {currentFeedback.summary}
            </Typography>
          </Box>

          <Tabs 
            value={activeFeedbackTab} 
            onChange={(e, newValue) => setActiveFeedbackTab(newValue)}
            sx={{ mb: 3 }}
          >
            <Tab label="Сильные стороны" />
            <Tab label="Что улучшить" />
            <Tab label="Советы" />
          </Tabs>

          {activeFeedbackTab === 0 && (
            <List>
              {currentFeedback.strengths?.map((strength, index) => (
                <ListItem key={index} sx={{ py: 1 }}>
                  <ListItemAvatar>
                    <Avatar sx={{ bgcolor: 'success.light' }}>
                      <ThumbUpIcon />
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText primary={strength} />
                </ListItem>
              ))}
            </List>
          )}

          {activeFeedbackTab === 1 && (
            <Box>
              <Typography variant="subtitle1" gutterBottom sx={{ color: 'error.main' }}>
                Области для улучшения:
              </Typography>
              <List>
                {currentFeedback.weaknesses?.map((weakness, index) => (
                  <ListItem key={index} sx={{ py: 1 }}>
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: 'error.light' }}>
                        <ErrorIcon />
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText primary={weakness} />
                  </ListItem>
                ))}
              </List>

              <Typography variant="subtitle1" gutterBottom sx={{ mt: 3, color: 'warning.main' }}>
                Частые ошибки:
              </Typography>
              <List>
                {currentFeedback.common_mistakes?.map((mistake, index) => (
                  <ListItem key={index} sx={{ py: 1 }}>
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: 'warning.light' }}>
                        <WarningIcon />
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText primary={mistake} />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}

          {activeFeedbackTab === 2 && (
            <List>
              {currentFeedback.tips?.map((tip, index) => (
                <ListItem key={index} sx={{ py: 1 }}>
                  <ListItemAvatar>
                    <Avatar sx={{ bgcolor: 'info.light' }}>
                      <TipsAndUpdatesIcon />
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText primary={tip} />
                </ListItem>
              ))}
            </List>
          )}

          <Accordion sx={{ mt: 3 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography>Рекомендации по развитию</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <List>
                {currentFeedback.improvement_areas?.map((area, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <DoneIcon color="primary" />
                    </ListItemIcon>
                    <ListItemText primary={area} />
                  </ListItem>
                ))}
              </List>
            </AccordionDetails>
          </Accordion>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFeedbackDialog(false)}>Закрыть</Button>
          <Button 
            variant="contained" 
            onClick={() => {
              setFeedbackDialog(false);
              setCurrentInterview(null);
            }}
          >
            Начать новое собеседование
          </Button>
        </DialogActions>
      </Dialog>
    );
  };

  const stats = getInterviewStats();

  return (
    <Container maxWidth="xl">
      <Typography variant="h4" gutterBottom>
        Подготовка к собеседованию
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Практикуйтесь с вопросами, сгенерированными ИИ на основе вашего резюме
      </Typography>

      <Grid container spacing={4}>
        {/* Левая колонка - настройки */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Настройки собеседования
            </Typography>
            
            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel>Выберите резюме</InputLabel>
              <Select
                value={selectedResume}
                onChange={(e) => setSelectedResume(e.target.value)}
                label="Выберите резюме"
              >
                {resumes.map((resume) => (
                  <MenuItem key={resume.id} value={resume.id}>
                    {resume.original_filename}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel>Тип собеседования</InputLabel>
              <Select
                value={interviewType}
                onChange={(e) => setInterviewType(e.target.value)}
                label="Тип собеседования"
              >
                {interviewTypes.map((type) => (
                  <MenuItem key={type.value} value={type.value}>
                    {type.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Alert severity="info" sx={{ mb: 3 }}>
              <Typography variant="body2">
                ИИ сгенерирует вопросы на основе выбранного резюме и типа собеседования
              </Typography>
            </Alert>

            <Button
              fullWidth
              variant="contained"
              size="large"
              onClick={generateInterview}
              disabled={generating || !selectedResume}
              startIcon={<PsychologyIcon />}
            >
              {generating ? 'Генерация...' : 'Начать собеседование'}
            </Button>
          </Paper>

          {/* Статистика */}
          {currentInterview && stats && (
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Прогресс
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Отвечено: {stats.answeredQuestions}/{stats.totalQuestions}
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={stats.progress} 
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </Box>
              <Button
                fullWidth
                variant="contained"
                color="success"
                onClick={completeInterview}
                startIcon={<CheckCircleIcon />}
                disabled={stats.answeredQuestions === 0 || generatingFeedback}
              >
                {generatingFeedback ? 'Анализируем...' : 'Завершить и получить анализ'}
              </Button>
            </Paper>
          )}
        </Grid>

        {/* Правая колонка - вопросы */}
        <Grid item xs={12} md={8}>
          {showAnalysisLoading ? (
            <LoadingAnimation
              title="Анализируем ваши ответы"
              message="ИИ анализирует ваши ответы, выявляет сильные стороны и области для улучшения. Это займет несколько секунд..."
              type="analysis"
            />
          ) : generating ? (
            <LoadingAnimation
              title="Генерируем вопросы"
              message="ИИ создает персонализированные вопросы на основе вашего резюме и выбранного типа собеседования..."
              type="questions"
            />
          ) : currentInterview ? (
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <PsychologyIcon sx={{ mr: 2, color: 'primary.main' }} />
                <Box>
                  <Typography variant="h5">
                    {interviewTypes.find(t => t.value === currentInterview.interview_type)?.label}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    На основе резюме: {resumes.find(r => r.id === selectedResume)?.original_filename}
                  </Typography>
                </Box>
              </Box>

              <Typography variant="body1" paragraph sx={{ mb: 3 }}>
                {currentInterview.preparation_tips || 'Отвечайте на вопросы, как на реальном собеседовании. После завершения вы получите детальный анализ ваших ответов.'}
              </Typography>

              <List>
                {currentInterview.questions?.map((question, index) => (
                  <React.Fragment key={index}>
                    <Card sx={{ mb: 2 }}>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Вопрос {index + 1}: {question.question}
                        </Typography>
                        
                        {question.category && (
                          <Chip 
                            label={question.category} 
                            size="small" 
                            sx={{ mb: 2 }}
                          />
                        )}

                        {question.tips && (
                          <Accordion sx={{ mb: 2 }}>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                              <Typography variant="body2">
                                <LightbulbIcon sx={{ fontSize: 16, mr: 1 }} />
                                Подсказки для ответа
                              </Typography>
                            </AccordionSummary>
                            <AccordionDetails>
                              <Typography variant="body2">
                                {question.tips}
                              </Typography>
                            </AccordionDetails>
                          </Accordion>
                        )}

                        <TextField
                          fullWidth
                          multiline
                          rows={4}
                          label="Ваш ответ"
                          value={userAnswers[index] || ''}
                          onChange={(e) => handleAnswerChange(index, e.target.value)}
                          placeholder="Введите ваш ответ здесь..."
                          variant="outlined"
                          sx={{ mt: 2 }}
                        />
                      </CardContent>
                    </Card>
                    <Divider />
                  </React.Fragment>
                ))}
              </List>
            </Paper>
          ) : (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <QuestionAnswerIcon sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Начните новое собеседование
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Выберите резюме и тип собеседования, затем нажмите "Начать собеседование"
              </Typography>
            </Paper>
          )}

          {/* История собеседований */}
          {completedInterviews.length > 0 && !showAnalysisLoading && !generating && (
            <Paper sx={{ p: 3, mt: 4 }}>
              <Typography variant="h6" gutterBottom>
                История собеседований
              </Typography>
              <List>
                {completedInterviews.slice(0, 3).map((interview, index) => (
                  <Card key={index} sx={{ mb: 2 }}>
                    <CardContent>
                      <Box display="flex" justifyContent="space-between" alignItems="center">
                        <Box>
                          <Typography variant="subtitle1" gutterBottom>
                            {interviewTypes.find(t => t.value === interview.interview_type)?.label}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Завершено: {new Date(interview.completedAt || interview.created_at).toLocaleDateString()}
                          </Typography>
                          <Typography variant="body2">
                            Количество вопросов: {interview.questions?.length || 0}
                          </Typography>
                          {interview.feedback?.overall_score && (
                            <Box display="flex" alignItems="center" sx={{ mt: 1 }}>
                              <StarIcon sx={{ color: '#FFD700', fontSize: 16, mr: 0.5 }} />
                              <Typography variant="body2">
                                Оценка: {interview.feedback.overall_score.toFixed(1)}/10
                              </Typography>
                            </Box>
                          )}
                        </Box>
                        <Button
                          variant="outlined"
                          onClick={() => loadFeedback(interview.id)}
                          disabled={loadingFeedback || showAnalysisLoading}
                        >
                          {loadingFeedback ? 'Загрузка...' : 'Посмотреть анализ'}
                        </Button>
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </List>
            </Paper>
          )}
        </Grid>
      </Grid>

      {/* Диалог с фидбеком */}
      {renderFeedbackDialog()}

      {/* Бекдроп для загрузки анализа */}
      <Backdrop
        sx={{ color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1 }}
        open={generatingFeedback && !showAnalysisLoading}
      >
        <Box sx={{ textAlign: 'center' }}>
          <CircularProgress color="inherit" size={60} thickness={4} />
          <Typography variant="h6" sx={{ mt: 2 }}>
            Завершаем собеседование...
          </Typography>
        </Box>
      </Backdrop>
    </Container>
  );
};

export default InterviewPage;