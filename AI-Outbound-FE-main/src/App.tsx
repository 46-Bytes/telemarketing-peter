import React from 'react';
import { AuthProvider } from './contexts/AuthContext';
import { MicrosoftAuthProvider } from './components/MicrosoftAuthProvider';
import AppRouter from './router/AppRouter';
import './App.css';

const App: React.FC = () => {
  return (
    <MicrosoftAuthProvider>
      <AuthProvider>
        <AppRouter />
      </AuthProvider>
    </MicrosoftAuthProvider>
  );
};

export default App;
