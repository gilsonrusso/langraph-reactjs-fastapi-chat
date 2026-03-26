import { Box, Card, CircularProgress, Typography } from '@mui/material';
import React from 'react';

export interface WeatherToolResult {
  temperature?: number;
  conditions?: string;
  humidity?: number;
  windSpeed?: number;
  feelsLike?: number;
}

export interface WeatherCardProps {
  args?: { location?: string };
  result?: WeatherToolResult;
  isLoading?: boolean;
}

function getThemeColor(conditions: string): string {
  if (!conditions) return '#667eea';
  const conditionLower = conditions.toLowerCase();
  if (conditionLower.includes('clear') || conditionLower.includes('sunny') || conditionLower.includes('ensolarado')) {
    return '#667eea';
  }
  if (conditionLower.includes('rain') || conditionLower.includes('storm') || conditionLower.includes('chuva')) {
    return '#4A5568';
  }
  if (conditionLower.includes('cloud') || conditionLower.includes('nublado') || conditionLower.includes('nuvens')) {
    return '#718096';
  }
  if (conditionLower.includes('snow') || conditionLower.includes('neve')) {
    return '#63B3ED';
  }
  return '#764ba2';
}

function WeatherIcon({ conditions }: { conditions: string }) {
  const iconBaseStyle = { width: 56, height: 56 };

  if (!conditions) return <CloudIcon style={{ ...iconBaseStyle, color: '#e5e7eb' }} />;

  const lower = conditions.toLowerCase();
  if (lower.includes('clear') || lower.includes('sunny') || lower.includes('ensolarado')) {
    return <SunIcon style={{ ...iconBaseStyle, color: '#fef08a' }} />;
  }
  if (lower.includes('rain') || lower.includes('drizzle') || lower.includes('chuva')) {
    return <RainIcon style={{ ...iconBaseStyle, color: '#bfdbfe' }} />;
  }
  return <CloudIcon style={{ ...iconBaseStyle, color: '#e5e7eb' }} />;
}

const SunIcon = ({ style }: { style: React.CSSProperties }) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" style={style}>
    <circle cx="12" cy="12" r="5" />
    <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" strokeWidth="2" stroke="currentColor" />
  </svg>
);

const RainIcon = ({ style }: { style: React.CSSProperties }) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" style={style}>
    <path d="M7 15a4 4 0 0 1 0-8 5 5 0 0 1 10 0 4 4 0 0 1 0 8H7z" fill="currentColor" opacity="0.8" />
    <path d="M8 18l2 4M12 18l2 4M16 18l2 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" fill="none" />
  </svg>
);

const CloudIcon = ({ style }: { style: React.CSSProperties }) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" style={style}>
    <path d="M7 15a4 4 0 0 1 0-8 5 5 0 0 1 10 0 4 4 0 0 1 0 8H7z" fill="currentColor" />
  </svg>
);

const WeatherCard: React.FC<WeatherCardProps> = ({ args, result, isLoading }) => {
  if (isLoading || !result) {
    return (
      <Card sx={{ bgcolor: '#667eea', color: 'white', p: 3, borderRadius: 3, maxWidth: 400, width: '100%', mb: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
        <CircularProgress size={24} sx={{ color: 'white' }} />
        <Typography>Consultando clima em {args?.location || '...'}</Typography>
      </Card>
    );
  }

  const themeColor = getThemeColor(result.conditions || 'clear');
  const tempC = result.temperature || 0;
  const tempF = ((tempC * 9) / 5 + 32).toFixed(1);

  return (
    <Card sx={{ bgcolor: themeColor, borderRadius: 3, mb: 2, maxWidth: 400, width: '100%' }}>
      <Box sx={{ bgcolor: 'rgba(255, 255, 255, 0.2)', p: 3, width: '100%' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'white', textTransform: 'capitalize' }}>
              {args?.location || 'Desconhecido'}
            </Typography>
            <Typography sx={{ color: 'white' }}>Clima Atual</Typography>
          </Box>
          <WeatherIcon conditions={result.conditions || ''} />
        </Box>

        <Box sx={{ mt: 3, display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' }}>
          <Typography variant="h3" sx={{ fontWeight: 'bold', color: 'white' }}>
            <span>{tempC}° C</span>
            <Typography component="span" sx={{ fontSize: '1rem', color: 'rgba(255,255,255,0.6)', ml: 1 }}>
              / {tempF}° F
            </Typography>
          </Typography>
          <Typography sx={{ color: 'white', textTransform: 'capitalize' }}>{result.conditions}</Typography>
        </Box>

        <Box sx={{ mt: 3, pt: 2, borderTop: '1px solid rgba(255,255,255,0.3)' }}>
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 2, textAlign: 'center' }}>
            <Box>
              <Typography sx={{ color: 'white', fontSize: '0.75rem' }}>Umidade</Typography>
              <Typography sx={{ color: 'white', fontWeight: 500 }}>{result.humidity || 0}%</Typography>
            </Box>
            <Box>
              <Typography sx={{ color: 'white', fontSize: '0.75rem' }}>Vento</Typography>
              <Typography sx={{ color: 'white', fontWeight: 500 }}>{(result.windSpeed || (result as any).wind_speed) || 0} km/h</Typography>
            </Box>
            <Box>
              <Typography sx={{ color: 'white', fontSize: '0.75rem' }}>Sensação</Typography>
              <Typography sx={{ color: 'white', fontWeight: 500 }}>{(result.feelsLike || (result as any).feels_like) || 0}°C</Typography>
            </Box>
          </Box>
        </Box>
      </Box>
    </Card>
  );
};

export default WeatherCard;
