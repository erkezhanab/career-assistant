import React from 'react';
import {
  Box,
  Typography,
  Radio,
  RadioGroup,
  FormControlLabel,
  Checkbox,
  FormGroup,
  TextField,
  Button,
  LinearProgress
} from '@mui/material';

const TestQuestion = ({ 
  question, 
  questionNumber, 
  totalQuestions,
  onAnswer,
  onComplete
}) => {
  const [answer, setAnswer] = React.useState('');

  const handleSubmit = () => {
    if (answer.trim()) {
      onAnswer(answer);
      setAnswer('');
    }
  };

  const progress = (questionNumber / totalQuestions) * 100;

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', mt: 3 }}>
      <Box sx={{ mb: 3 }}>
        <LinearProgress variant="determinate" value={progress} sx={{ mb: 1 }} />
        <Typography variant="body2" color="text.secondary">
          Вопрос {questionNumber} из {totalQuestions}
        </Typography>
      </Box>

      <Typography variant="h6" gutterBottom>
        {question.question_text}
      </Typography>

      {question.question_type === 'single_choice' && (
        <RadioGroup value={answer} onChange={(e) => setAnswer(e.target.value)}>
          {question.options.map((option, index) => (
            <FormControlLabel
              key={index}
              value={option}
              control={<Radio />}
              label={option}
              sx={{ mb: 1 }}
            />
          ))}
        </RadioGroup>
      )}

      {question.question_type === 'multiple_choice' && (
        <FormGroup>
          {question.options.map((option, index) => (
            <FormControlLabel
              key={index}
              control={
                <Checkbox 
                  checked={answer.includes(option)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setAnswer([...answer, option]);
                    } else {
                      setAnswer(answer.filter(a => a !== option));
                    }
                  }}
                />
              }
              label={option}
              sx={{ mb: 1 }}
            />
          ))}
        </FormGroup>
      )}

      {question.question_type === 'open_ended' && (
        <TextField
          fullWidth
          multiline
          rows={4}
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          placeholder="Введите ваш ответ..."
          sx={{ mb: 2 }}
        />
      )}

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={!answer || (Array.isArray(answer) && answer.length === 0)}
        >
          {questionNumber === totalQuestions ? 'Завершить тест' : 'Следующий вопрос'}
        </Button>
      </Box>
    </Box>
  );
};

export default TestQuestion;