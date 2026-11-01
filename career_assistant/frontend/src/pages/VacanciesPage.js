import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  TextField,
  Button,
  Box,
  Typography,
  Card,
  CardContent,
  CardActions,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Alert,
  IconButton,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Search as SearchIcon,
  LocationOn,
  Business,
  AttachMoney,
  Schedule,
  Bookmark,
  BookmarkBorder,
} from '@mui/icons-material';
import { vacanciesAPI, applicationsAPI } from '../api';
import { toast } from 'react-toastify';

const VacanciesPage = () => {
  const [searchParams, setSearchParams] = useState({
    position: '',
    city: '',
    salary_desired: '',
    programming_languages: [],
  });
  const [vacancies, setVacancies] = useState([]);
  const [initialVacancies, setInitialVacancies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedVacancy, setSelectedVacancy] = useState(null);
  const [coverLetterDialog, setCoverLetterDialog] = useState(false);
  const [letterStyle, setLetterStyle] = useState('formal');
  const [generatedLetter, setGeneratedLetter] = useState('');
  const [activeTab, setActiveTab] = useState(0);
  const [savedVacancies, setSavedVacancies] = useState([]);

  const programmingLanguages = [
    'JavaScript','Python','Java','C#','PHP','TypeScript','Ruby','Go','Swift','Kotlin',
  ];

  const cities = [
    'Астана','Алматы','Шымкент','Караганда','Актобе','Тараз','Павлодар',
    'Усть-Каменогорск','Семей','Костанай','Петропавловск','Уральск',
    'Атырау','Актау','Кызылорда',
  ];

  // Загружаем начальные вакансии при монтировании
  useEffect(() => {
    loadInitialVacancies();
  }, []);

  const loadInitialVacancies = async () => {
    try {
      setLoading(true);
      const response = await vacanciesAPI.getVacancies();
      const data = Array.isArray(response.data) ? response.data : [];
      setVacancies(data);
      setInitialVacancies(data);
    } catch (error) {
      console.error('Error loading vacancies:', error);
      toast.error('Ошибка загрузки вакансий');
      setVacancies([]);
      setInitialVacancies([]);
    } finally {
      setLoading(false);
    }
  };

const handleSearch = async () => {
  if (!searchParams.position.trim()) {
    toast.error('Введите должность для поиска');
    return;
  }

  setLoading(true);
  try {
    // Просто передаем все как есть, конвертацию сделаем на бэкенде
    const payload = {
      position: searchParams.position.trim(),
      city: searchParams.city || '',
      salary_desired: searchParams.salary_desired ? parseInt(searchParams.salary_desired) : null,
      programming_languages: searchParams.programming_languages || [],
    };

    console.log('Sending search payload:', payload); // для отладки

    const response = await vacanciesAPI.searchVacancies(payload);

    if (Array.isArray(response.data)) {
      setVacancies(response.data);
      toast.success(`Найдено ${response.data.length} вакансий`);
    } else {
      // Бэкенд вернул не массив, а объект-сообщение
      // (например, { message: '...', suggestions: [...] } если ничего не найдено)
      setVacancies([]);
      toast.info(response.data?.message || 'Вакансии не найдены');
    }
  } catch (error) {
    console.error('Search error:', error.response || error);
    const errorMsg = error.response?.data?.error || 
                    error.response?.data?.message || 
                    'Ошибка при поиске вакансий';
    toast.error(errorMsg);
  } finally {
    setLoading(false);
  }
};

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  // Функция для фильтрации уже загруженных вакансий (локальная фильтрация)
  const filterVacancies = () => {
    if (!searchParams.position && !searchParams.city && !searchParams.salary_desired && 
        searchParams.programming_languages.length === 0) {
      // Если все фильтры пустые, показываем все вакансии
      setVacancies(initialVacancies);
      return;
    }

    const filtered = initialVacancies.filter(vacancy => {
      // Фильтр по должности
      if (searchParams.position && 
          !vacancy.name.toLowerCase().includes(searchParams.position.toLowerCase())) {
        return false;
      }

      // Фильтр по городу
      if (searchParams.city && vacancy.city !== searchParams.city) {
        return false;
      }

      // Фильтр по зарплате
      if (searchParams.salary_desired) {
        const minSalary = parseInt(searchParams.salary_desired);
        if (!vacancy.salary_from || vacancy.salary_from < minSalary) {
          return false;
        }
      }

      // Фильтр по языкам программирования
      if (searchParams.programming_languages.length > 0) {
        const vacancySkills = vacancy.skills?.join(' ').toLowerCase() || '';
        const vacancyDescription = vacancy.description?.toLowerCase() || '';
        const vacancyText = (vacancySkills + ' ' + vacancyDescription + ' ' + vacancy.name).toLowerCase();
        
        const hasLanguage = searchParams.programming_languages.some(lang => 
          vacancyText.includes(lang.toLowerCase())
        );
        
        if (!hasLanguage) {
          return false;
        }
      }

      return true;
    });

    setVacancies(filtered);
    if (filtered.length === 0 && initialVacancies.length > 0) {
      toast.info('По вашим фильтрам не найдено вакансий. Попробуйте расширить критерии поиска.');
    }
  };

  const handleGenerateCoverLetter = async () => {
    if (!selectedVacancy) return;
    try {
      const response = await applicationsAPI.generateCoverLetter({
        vacancy_id: selectedVacancy.id,
        style: letterStyle,
      });
      setGeneratedLetter(response.data.letter);
    } catch (error) {
      toast.error('Ошибка генерации письма');
    }
  };

  const handleApply = async () => {
    if (!selectedVacancy || !generatedLetter) {
      toast.error('Заполните сопроводительное письмо');
      return;
    }

    try {
      await applicationsAPI.apply({
        vacancy_id: selectedVacancy.id,
        cover_letter: generatedLetter,
        letter_style: letterStyle,
      });
      toast.success('Отклик отправлен успешно!');
      setCoverLetterDialog(false);
      setGeneratedLetter('');
    } catch (error) {
      toast.error('Ошибка при отправке отклика');
    }
  };

  const toggleSaveVacancy = (vacancy) => {
    const isSaved = savedVacancies.some(v => v.id === vacancy.id);
    if (isSaved) {
      setSavedVacancies(savedVacancies.filter(v => v.id !== vacancy.id));
      toast.info('Вакансия удалена из избранного');
    } else {
      setSavedVacancies([...savedVacancies, vacancy]);
      toast.success('Вакансия добавлена в избранное');
    }
  };

  const isVacancySaved = (vacancyId) => savedVacancies.some(v => v.id === vacancyId);

  return (
    <Container maxWidth="xl">
      <Typography variant="h4" gutterBottom>
        Поиск вакансий
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Найдите подходящие вакансии по вашим навыкам и предпочтениям
      </Typography>

      <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
        <Tab label="Поиск вакансий" />
        <Tab label="Избранное" />
      </Tabs>

      {activeTab === 0 ? (
        <>
          {/* Форма поиска */}
          <Paper sx={{ p: 3, mb: 4 }}>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  label="Должность"
                  value={searchParams.position}
                  onChange={(e) => setSearchParams({...searchParams, position: e.target.value})}
                  onKeyPress={handleKeyPress}
                  placeholder="Например: Frontend разработчик"
                />
              </Grid>
              <Grid item xs={12} md={2}>
                <FormControl fullWidth>
                  <InputLabel>Город</InputLabel>
                  <Select
                    value={searchParams.city}
                    onChange={(e) => setSearchParams({...searchParams, city: e.target.value})}
                    label="Город"
                  >
                    <MenuItem value="">Любой город</MenuItem>
                    {cities.map(city => (
                      <MenuItem key={city} value={city}>{city}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={2}>
                <TextField
                  fullWidth
                  label="Зарплата от"
                  type="number"
                  value={searchParams.salary_desired}
                  onChange={(e) => setSearchParams({...searchParams, salary_desired: e.target.value})}
                  onKeyPress={handleKeyPress}
                  placeholder="50000"
                  InputProps={{ inputProps: { min: 0 } }}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <FormControl fullWidth>
                  <InputLabel>Языки программирования</InputLabel>
                  <Select
                    multiple
                    value={searchParams.programming_languages}
                    onChange={(e) => setSearchParams({...searchParams, programming_languages: e.target.value})}
                    renderValue={(selected) => selected.join(', ')}
                    label="Языки программирования"
                  >
                    {programmingLanguages.map((lang) => (
                      <MenuItem key={lang} value={lang}>{lang}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={1}>
                <Button
                  fullWidth
                  variant="contained"
                  startIcon={<SearchIcon />}
                  onClick={handleSearch}
                  disabled={loading}
                  sx={{ height: '56px' }}
                >
                  {loading ? 'Поиск...' : 'Найти'}
                </Button>
              </Grid>
              <Grid item xs={12} md={1}>
                <Button
                  fullWidth
                  variant="outlined"
                  onClick={filterVacancies}
                  disabled={loading}
                  sx={{ height: '56px' }}
                >
                  Фильтры
                </Button>
              </Grid>
            </Grid>
          </Paper>

          {/* Результаты поиска */}
          <Grid container spacing={3}>
            {loading ? (
              <Grid item xs={12}>
                <Alert severity="info">Загрузка вакансий...</Alert>
              </Grid>
            ) : vacancies.length === 0 ? (
              <Grid item xs={12}>
                <Alert severity="info">
                  Вакансий не найдено. Попробуйте изменить критерии поиска.
                </Alert>
              </Grid>
            ) : (
              vacancies.map((vacancy) => (
                <Grid item xs={12} key={vacancy.id}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <Box>
                          <Typography variant="h6" gutterBottom>{vacancy.name}</Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                            <Chip icon={<Business />} label={vacancy.company} size="small" variant="outlined" />
                            <Chip icon={<LocationOn />} label={vacancy.city} size="small" variant="outlined" />
                            {vacancy.salary_from && (
                              <Chip
                                icon={<AttachMoney />}
                                label={`${vacancy.salary_from} - ${vacancy.salary_to || ''} ${vacancy.salary_currency || '₽'}`}
                                size="small"
                                color="success"
                              />
                            )}
                            {vacancy.experience && (
                              <Chip icon={<Schedule />} label={vacancy.experience} size="small" variant="outlined" />
                            )}
                          </Box>
                        </Box>
                        <IconButton onClick={() => toggleSaveVacancy(vacancy)}>
                          {isVacancySaved(vacancy.id) ? <Bookmark color="primary" /> : <BookmarkBorder />}
                        </IconButton>
                      </Box>

                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{ mb: 2, display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}
                        dangerouslySetInnerHTML={{ __html: vacancy.description }}
                      />

                      {vacancy.skills && vacancy.skills.length > 0 && (
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="subtitle2" gutterBottom>Ключевые навыки:</Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {vacancy.skills.slice(0, 5).map((skill, index) => (
                              <Chip key={index} label={skill} size="small" />
                            ))}
                            {vacancy.skills.length > 5 && (
                              <Chip label={`+${vacancy.skills.length - 5}`} size="small" variant="outlined" />
                            )}
                          </Box>
                        </Box>
                      )}
                    </CardContent>
                    <CardActions>
                      <Button size="small" onClick={() => window.open(vacancy.url, '_blank')}>На HH.ru</Button>
                      <Button size="small" variant="contained" onClick={() => { setSelectedVacancy(vacancy); setCoverLetterDialog(true); }}>Откликнуться</Button>
                    </CardActions>
                  </Card>
                </Grid>
              ))
            )}
          </Grid>
        </>
      ) : (
        /* Избранное */
        <Grid container spacing={3}>
          {savedVacancies.length === 0 ? (
            <Grid item xs={12}>
              <Alert severity="info">У вас пока нет избранных вакансий</Alert>
            </Grid>
          ) : (
            savedVacancies.map((vacancy) => (
              <Grid item xs={12} key={vacancy.id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <Box>
                        <Typography variant="h6" gutterBottom>{vacancy.name}</Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                          <Chip icon={<Business />} label={vacancy.company} size="small" />
                          <Chip icon={<LocationOn />} label={vacancy.city} size="small" />
                        </Box>
                      </Box>
                      <IconButton onClick={() => toggleSaveVacancy(vacancy)}><Bookmark color="primary" /></IconButton>
                    </Box>
                    <Button variant="contained" onClick={() => { setSelectedVacancy(vacancy); setCoverLetterDialog(true); }}>Откликнуться</Button>
                  </CardContent>
                </Card>
              </Grid>
            ))
          )}
        </Grid>
      )}

      {/* Диалог сопроводительного письма */}
      <Dialog open={coverLetterDialog} onClose={() => setCoverLetterDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Сопроводительное письмо для: {selectedVacancy?.name}</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mb: 3, mt: 2 }}>
            <InputLabel>Стиль письма</InputLabel>
            <Select value={letterStyle} onChange={(e) => setLetterStyle(e.target.value)} label="Стиль письма">
              <MenuItem value="formal">Официальный</MenuItem>
              <MenuItem value="friendly">Дружелюбный</MenuItem>
              <MenuItem value="brief">Краткий</MenuItem>
              <MenuItem value="creative">Креативный</MenuItem>
            </Select>
          </FormControl>
          <Button variant="outlined" onClick={handleGenerateCoverLetter} sx={{ mb: 2 }}>Сгенерировать письмо с помощью ИИ</Button>
          {generatedLetter && (
            <>
              <Alert severity="info" sx={{ mb: 2 }}>Письмо сгенерировано ИИ. Отредактируйте при необходимости.</Alert>
              <TextField fullWidth multiline rows={10} value={generatedLetter} onChange={(e) => setGeneratedLetter(e.target.value)} variant="outlined" placeholder="Сгенерируйте или напишите сопроводительное письмо..." />
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCoverLetterDialog(false)}>Отмена</Button>
          <Button variant="contained" onClick={handleApply} disabled={!generatedLetter}>Отправить отклик</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default VacanciesPage;