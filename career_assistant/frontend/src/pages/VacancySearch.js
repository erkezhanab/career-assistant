// frontend/src/pages/VacancySearch.jsx
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
} from '@mui/material';
import {
  Search as SearchIcon,
  LocationOn,
  Business,
  AttachMoney,
  Schedule,
} from '@mui/icons-material';
import axios from '../api/axiosConfig';

const VacancySearch = () => {
  const [searchParams, setSearchParams] = useState({
    position: '',
    city: '',
    salary: '',
    programmingLanguages: [],
  });
  
  const [vacancies, setVacancies] = useState([]);
  const [selectedVacancy, setSelectedVacancy] = useState(null);
  const [coverLetterDialog, setCoverLetterDialog] = useState(false);
  const [letterStyle, setLetterStyle] = useState('formal');
  const [generatedLetter, setGeneratedLetter] = useState('');

  const programmingLanguages = [
    'JavaScript',
    'Python',
    'Java',
    'C#',
    'PHP',
    'TypeScript',
    'Ruby',
    'Go',
    'Swift',
    'Kotlin',
    'Rust',
    'Scala',
  ];

  const searchVacancies = async () => {
    try {
      const response = await axios.post('/vacancies/search/', searchParams);
      setVacancies(response.data);
    } catch (error) {
      console.error('Search failed:', error);
    }
  };

  const handleGenerateCoverLetter = async () => {
    try {
      const response = await axios.post('/applications/generate-letter/', {
        vacancy_id: selectedVacancy.id,
        style: letterStyle,
      });
      setGeneratedLetter(response.data.letter);
    } catch (error) {
      console.error('Failed to generate letter:', error);
    }
  };

  const handleApply = async () => {
    try {
      await axios.post('/applications/apply/', {
        vacancy_id: selectedVacancy.id,
        cover_letter: generatedLetter,
        letter_style: letterStyle,
      });
      setCoverLetterDialog(false);
      // Показать уведомление об успехе
    } catch (error) {
      console.error('Application failed:', error);
    }
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Поиск вакансий
        </Typography>
      </Box>

      {/* Форма поиска */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              label="Должность"
              value={searchParams.position}
              onChange={(e) => setSearchParams({...searchParams, position: e.target.value})}
            />
          </Grid>
          <Grid item xs={12} md={2}>
            <TextField
              fullWidth
              label="Город"
              value={searchParams.city}
              onChange={(e) => setSearchParams({...searchParams, city: e.target.value})}
            />
          </Grid>
          <Grid item xs={12} md={2}>
            <TextField
              fullWidth
              label="Зарплата от"
              type="number"
              value={searchParams.salary}
              onChange={(e) => setSearchParams({...searchParams, salary: e.target.value})}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Языки программирования</InputLabel>
              <Select
                multiple
                value={searchParams.programmingLanguages}
                onChange={(e) => setSearchParams({...searchParams, programmingLanguages: e.target.value})}
                renderValue={(selected) => selected.join(', ')}
              >
                {programmingLanguages.map((lang) => (
                  <MenuItem key={lang} value={lang}>
                    {lang}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={2}>
            <Button
              fullWidth
              variant="contained"
              startIcon={<SearchIcon />}
              onClick={searchVacancies}
              sx={{ height: '56px' }}
            >
              Найти
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Список вакансий */}
      <Grid container spacing={3}>
        {vacancies.map((vacancy) => (
          <Grid item xs={12} key={vacancy.id}>
            <Card>
              <CardContent>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={8}>
                    <Typography variant="h6" gutterBottom>
                      {vacancy.name}
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                      <Chip
                        icon={<Business />}
                        label={vacancy.company}
                        size="small"
                      />
                      <Chip
                        icon={<LocationOn />}
                        label={vacancy.city}
                        size="small"
                      />
                      {vacancy.salary_from && (
                        <Chip
                          icon={<AttachMoney />}
                          label={`${vacancy.salary_from} - ${vacancy.salary_to || ''} ${vacancy.salary_currency}`}
                          size="small"
                          color="success"
                        />
                      )}
                      <Chip
                        icon={<Schedule />}
                        label={vacancy.experience}
                        size="small"
                      />
                    </Box>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      dangerouslySetInnerHTML={{ __html: vacancy.description.slice(0, 300) + '...' }}
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Ключевые навыки:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {vacancy.skills.slice(0, 5).map((skill, index) => (
                          <Chip key={index} label={skill} size="small" />
                        ))}
                      </Box>
                      <Button
                        variant="outlined"
                        onClick={() => {
                          setSelectedVacancy(vacancy);
                          // Открыть модалку с деталями
                        }}
                      >
                        Подробнее
                      </Button>
                      <Button
                        variant="contained"
                        onClick={() => {
                          setSelectedVacancy(vacancy);
                          setCoverLetterDialog(true);
                        }}
                      >
                        Откликнуться
                      </Button>
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Диалог сопроводительного письма */}
      <Dialog
        open={coverLetterDialog}
        onClose={() => setCoverLetterDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Сопроводительное письмо</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mb: 3 }}>
            <InputLabel>Стиль письма</InputLabel>
            <Select
              value={letterStyle}
              onChange={(e) => setLetterStyle(e.target.value)}
              label="Стиль письма"
            >
              <MenuItem value="formal">Официальный</MenuItem>
              <MenuItem value="friendly">Дружелюбный</MenuItem>
              <MenuItem value="brief">Краткий</MenuItem>
              <MenuItem value="creative">Креативный</MenuItem>
            </Select>
          </FormControl>

          <Button
            variant="outlined"
            onClick={handleGenerateCoverLetter}
            sx={{ mb: 2 }}
          >
            Сгенерировать письмо
          </Button>

          {generatedLetter && (
            <>
              <Alert severity="info" sx={{ mb: 2 }}>
                Письмо сгенерировано ИИ. Отредактируйте при необходимости.
              </Alert>
              <TextField
                fullWidth
                multiline
                rows={10}
                value={generatedLetter}
                onChange={(e) => setGeneratedLetter(e.target.value)}
                variant="outlined"
              />
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCoverLetterDialog(false)}>Отмена</Button>
          <Button
            variant="contained"
            onClick={handleApply}
            disabled={!generatedLetter}
          >
            Отправить отклик
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default VacancySearch;