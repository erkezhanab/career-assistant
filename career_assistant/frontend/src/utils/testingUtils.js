// Форматирование времени
export const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

// Расчет прогресса
export const calculateProgress = (current, total) => {
  return total > 0 ? Math.round((current / total) * 100) : 0;
};

// Валидация сертификата
export const validateCertificate = (data) => {
  const errors = {};
  
  if (!data.title?.trim()) errors.title = 'Название обязательно';
  if (!data.issuer?.trim()) errors.issuer = 'Организация обязательна';
  if (!data.issue_date) errors.issue_date = 'Дата выдачи обязательна';
  
  // Проверка даты
  if (data.issue_date) {
    const issueDate = new Date(data.issue_date);
    const today = new Date();
    if (issueDate > today) {
      errors.issue_date = 'Дата выдачи не может быть в будущем';
    }
  }
  
  if (data.expiry_date && data.issue_date) {
    const issueDate = new Date(data.issue_date);
    const expiryDate = new Date(data.expiry_date);
    if (expiryDate < issueDate) {
      errors.expiry_date = 'Дата окончания не может быть раньше даты выдачи';
    }
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};

// Форматирование результата теста
export const formatTestResult = (result) => {
  const passed = result.score >= result.passing_score;
  const scorePercentage = Math.round(result.score);
  
  return {
    passed,
    score: scorePercentage,
    correctCount: result.correct_count,
    totalQuestions: result.total_questions,
    timeSpent: result.time_spent_seconds,
    canRetake: result.can_retake,
    nextRetakeDate: result.next_retake_date,
    detailedResults: result.detailed_results || [],
    categoryName: result.category_name,
    completedAt: result.completed_at
  };
};

// Подсчет оставшегося времени
export const calculateRemainingTime = (startTime, timeLimitMinutes, timeSpentSeconds = 0) => {
  if (!startTime) return timeLimitMinutes * 60;
  
  const now = new Date().getTime();
  const start = new Date(startTime).getTime();
  const elapsed = Math.floor((now - start) / 1000);
  const remaining = (timeLimitMinutes * 60) - elapsed - timeSpentSeconds;
  
  return Math.max(0, remaining);
};

// Определение цвета в зависимости от оценки
export const getScoreColor = (score) => {
  if (score >= 90) return '#4CAF50'; // Зеленый
  if (score >= 70) return '#8BC34A'; // Светло-зеленый
  if (score >= 50) return '#FFC107'; // Желтый
  if (score >= 30) return '#FF9800'; // Оранжевый
  return '#F44336'; // Красный
};

// Обработка ответов на разные типы вопросов
export const processAnswer = (questionType, answer) => {
  if (questionType === 'multiple_choice') {
    return Array.isArray(answer) ? answer : [answer];
  }
  return answer;
};