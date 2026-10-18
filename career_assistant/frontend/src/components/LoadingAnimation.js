import React from 'react';
import { Box, Typography, CircularProgress, keyframes } from '@mui/material';
import { AutoAwesome, Psychology, QuestionAnswer, Lightbulb } from '@mui/icons-material';

const pulse = keyframes`
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.7; }
  100% { transform: scale(1); opacity: 1; }
`;

const float = keyframes`
  0% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
  100% { transform: translateY(0px); }
`;

const LoadingAnimation = ({ title, message, type = 'analysis' }) => {
  const getIcon = () => {
    switch(type) {
      case 'questions':
        return <QuestionAnswer sx={{ fontSize: 60, color: 'primary.main' }} />;
      case 'analysis':
        return <Psychology sx={{ fontSize: 60, color: 'secondary.main' }} />;
      default:
        return <AutoAwesome sx={{ fontSize: 60, color: 'primary.main' }} />;
    }
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        p: 4,
        textAlign: 'center',
        minHeight: '300px',
        bgcolor: 'background.paper',
        borderRadius: 2,
        border: '1px solid',
        borderColor: 'divider',
      }}
    >
      <Box
        sx={{
          position: 'relative',
          mb: 3,
        }}
      >
        {/* Анимированный фон */}
        <Box
          sx={{
            position: 'absolute',
            top: -20,
            left: -20,
            width: 100,
            height: 100,
            borderRadius: '50%',
            bgcolor: type === 'analysis' ? 'secondary.light' : 'primary.light',
            opacity: 0.2,
            animation: `${pulse} 2s infinite ease-in-out`,
          }}
        />
        
        {/* Плавающая иконка */}
        <Box
          sx={{
            position: 'relative',
            animation: `${float} 3s infinite ease-in-out`,
          }}
        >
          {getIcon()}
        </Box>
        
        {/* Вращающиеся элементы вокруг */}
        <CircularProgress
          size={80}
          thickness={2}
          sx={{
            position: 'absolute',
            top: -10,
            left: -10,
            color: type === 'analysis' ? 'secondary.main' : 'primary.main',
          }}
        />
      </Box>

      <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
        {title}
      </Typography>
      
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3, maxWidth: '400px' }}>
        {message}
      </Typography>

      <Box sx={{ position: 'relative', display: 'inline-flex' }}>
        <CircularProgress
          size={40}
          thickness={4}
          sx={{
            color: type === 'analysis' ? 'secondary.main' : 'primary.main',
          }}
        />
        <Box
          sx={{
            top: 0,
            left: 0,
            bottom: 0,
            right: 0,
            position: 'absolute',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Lightbulb fontSize="small" />
        </Box>
      </Box>

      {/* Анимированные точки */}
      <Box sx={{ display: 'flex', mt: 3, gap: 1 }}>
        {[0, 1, 2].map((i) => (
          <Box
            key={i}
            sx={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              bgcolor: type === 'analysis' ? 'secondary.main' : 'primary.main',
              animation: `${pulse} 1.5s infinite ease-in-out`,
              animationDelay: `${i * 0.2}s`,
            }}
          />
        ))}
      </Box>
    </Box>
  );
};

export default LoadingAnimation;