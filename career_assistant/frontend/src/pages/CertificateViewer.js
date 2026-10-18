// CertificateViewer.jsx
import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
  Typography,
  Box,
  Button,
  Grid,
  Chip,
  Divider,
  CircularProgress
} from '@mui/material';
import {
  Close,
  ArrowBack,
  ArrowForward,
  ZoomIn,
  ZoomOut,
  Download,
  Fullscreen,
  FullscreenExit,
  CheckCircle,
  Description as DescriptionIcon
} from '@mui/icons-material';

const CertificateViewer = ({ 
  open, 
  onClose, 
  documents,
  currentIndex = 0 
}) => {
  const [currentDocIndex, setCurrentDocIndex] = useState(currentIndex);
  const [zoom, setZoom] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [loading, setLoading] = useState(false);

  const currentDocument = documents[currentDocIndex];

  const handlePrev = () => {
    if (currentDocIndex > 0) {
      setCurrentDocIndex(prev => prev - 1);
      setZoom(1); // Сброс зума при смене документа
    }
  };

  const handleNext = () => {
    if (currentDocIndex < documents.length - 1) {
      setCurrentDocIndex(prev => prev + 1);
      setZoom(1); // Сброс зума при смене документа
    }
  };

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev + 0.25, 3));
  };

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev - 0.25, 0.5));
  };

  const handleDownload = () => {
    if (!currentDocument?.file_url) return;
    
    setLoading(true);
    try {
      const link = document.createElement('a');
      link.href = currentDocument.file_url;
      link.download = `${currentDocument.title}.${currentDocument.file_url.split('.').pop()}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('Ошибка загрузки файла:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleFullscreen = () => {
    if (!isFullscreen) {
      const elem = document.querySelector('.certificate-viewer-content');
      if (elem.requestFullscreen) {
        elem.requestFullscreen();
      } else if (elem.webkitRequestFullscreen) { /* Safari */
        elem.webkitRequestFullscreen();
      } else if (elem.msRequestFullscreen) { /* IE11 */
        elem.msRequestFullscreen();
      }
      setIsFullscreen(true);
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      } else if (document.webkitExitFullscreen) { /* Safari */
        document.webkitExitFullscreen();
      } else if (document.msExitFullscreen) { /* IE11 */
        document.msExitFullscreen();
      }
      setIsFullscreen(false);
    }
  };

  // Обработчик выхода из полноэкранного режима
  React.useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);

  const renderDocumentContent = () => {
    if (!currentDocument) return null;

    const fileExtension = currentDocument.file_url?.split('.').pop()?.toLowerCase();

    if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(fileExtension)) {
      return (
        <Box
          sx={{
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            overflow: 'auto',
            bgcolor: 'grey.100',
            borderRadius: 1
          }}
        >
          <img
            src={currentDocument.file_url}
            alt={currentDocument.title}
            style={{
              maxWidth: '100%',
              maxHeight: '100%',
              transform: `scale(${zoom})`,
              transition: 'transform 0.3s ease',
              objectFit: 'contain'
            }}
            onLoad={() => setLoading(false)}
            onError={() => setLoading(false)}
          />
        </Box>
      );
    } else if (fileExtension === 'pdf') {
      return (
        <Box
          sx={{
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            overflow: 'auto',
            bgcolor: 'grey.100',
            borderRadius: 1
          }}
        >
          <iframe
            src={currentDocument.file_url}
            title={currentDocument.title}
            style={{
              width: '100%',
              height: '100%',
              border: 'none',
              transform: `scale(${zoom})`,
              transformOrigin: 'center center'
            }}
            onLoad={() => setLoading(false)}
          />
        </Box>
      );
    } else {
      return (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            p: 3,
            textAlign: 'center'
          }}
        >
          <DescriptionIcon sx={{ fontSize: 60, color: 'grey.400', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
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

  if (!currentDocument) return null;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      fullScreen={isFullscreen}
      sx={{
        '& .MuiDialog-paper': {
          height: isFullscreen ? '100vh' : '80vh',
          maxHeight: 'none'
        }
      }}
    >
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box>
            <Typography variant="h6" noWrap>
              {currentDocument.title}
            </Typography>
            <Typography variant="body2" color="text.secondary" noWrap>
              {currentDocument.issuer} • {new Date(currentDocument.issue_date).toLocaleDateString()}
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 1 }}>
            {currentDocument.is_verified && (
              <Chip
                icon={<CheckCircle />}
                label="Проверен"
                size="small"
                color="success"
                variant="outlined"
              />
            )}
            <Chip
              label={currentDocument.document_type === 'diploma' ? 'Диплом' : 
                     currentDocument.document_type === 'course' ? 'Курс' : 'Сертификат'}
              size="small"
              variant="outlined"
            />
          </Box>
        </Box>
        
        <IconButton onClick={onClose}>
          <Close />
        </IconButton>
      </DialogTitle>
      
      <Divider />
      
      <DialogContent dividers sx={{ p: 0, overflow: 'hidden' }}>
        <Box
          className="certificate-viewer-content"
          sx={{
            height: '100%',
            display: 'flex',
            flexDirection: 'column'
          }}
        >
          {/* Панель управления */}
          <Box
            sx={{
              p: 2,
              bgcolor: 'grey.50',
              borderBottom: 1,
              borderColor: 'divider',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Button
                size="small"
                startIcon={<ArrowBack />}
                onClick={handlePrev}
                disabled={currentDocIndex === 0}
              >
                Предыдущий
              </Button>
              
              <Typography variant="body2">
                {currentDocIndex + 1} из {documents.length}
              </Typography>
              
              <Button
                size="small"
                endIcon={<ArrowForward />}
                onClick={handleNext}
                disabled={currentDocIndex === documents.length - 1}
              >
                Следующий
              </Button>
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" sx={{ mr: 1 }}>
                Масштаб: {Math.round(zoom * 100)}%
              </Typography>
              
              <IconButton
                size="small"
                onClick={handleZoomOut}
                disabled={zoom <= 0.5}
              >
                <ZoomOut />
              </IconButton>
              
              <Button
                size="small"
                variant="outlined"
                onClick={() => setZoom(1)}
              >
                100%
              </Button>
              
              <IconButton
                size="small"
                onClick={handleZoomIn}
                disabled={zoom >= 3}
              >
                <ZoomIn />
              </IconButton>
              
              <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />
              
              <IconButton
                size="small"
                onClick={toggleFullscreen}
              >
                {isFullscreen ? <FullscreenExit /> : <Fullscreen />}
              </IconButton>
              
              <Button
                size="small"
                variant="contained"
                startIcon={<Download />}
                onClick={handleDownload}
                disabled={loading || !currentDocument.file_url}
                sx={{ ml: 1 }}
              >
                {loading ? <CircularProgress size={20} /> : 'Скачать'}
              </Button>
            </Box>
          </Box>
          
          {/* Контент документа */}
          <Box sx={{ flex: 1, position: 'relative', overflow: 'auto' }}>
            {loading && (
              <Box
                sx={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  bgcolor: 'rgba(255, 255, 255, 0.8)',
                  zIndex: 1
                }}
              >
                <CircularProgress />
              </Box>
            )}
            
            {renderDocumentContent()}
          </Box>
        </Box>
      </DialogContent>
    </Dialog>
  );
};

export default CertificateViewer;