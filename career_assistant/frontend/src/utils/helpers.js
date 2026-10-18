export const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
};

export const formatSalary = (from, to, currency) => {
  if (!from && !to) return 'Не указана';
  
  const formattedCurrency = currency === 'RUR' ? '₽' : currency;
  
  if (from && to) {
    return `${from} - ${to} ${formattedCurrency}`;
  } else if (from) {
    return `от ${from} ${formattedCurrency}`;
  } else if (to) {
    return `до ${to} ${formattedCurrency}`;
  }
  
  return 'Не указана';
};

export const truncateText = (text, maxLength = 100) => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

export const isValidEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
};

export const downloadFile = (url, filename) => {
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};