import { createTheme, useMediaQuery } from '@mui/material';
import { useMemo } from 'react';

export const useAppTheme = () => {
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');

  return useMemo(
    () =>
      createTheme({
        palette: {
          mode: prefersDarkMode ? 'dark' : 'light',
          primary: {
            main: '#4285f4',
          },
          secondary: {
            main: '#9334e6',
          },
          background: {
            default: prefersDarkMode ? '#131314' : '#ffffff',
            paper: prefersDarkMode ? '#1e1e20' : '#f0f4f9',
          },
        },
        typography: {
          fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
          h6: {
            fontWeight: 500,
          },
        },
        shape: {
          borderRadius: 12,
        },
        components: {
          MuiPaper: {
            styleOverrides: {
              root: {
                backgroundImage: 'none',
              },
            },
          },
        },
      }),
    [prefersDarkMode]
  );
};