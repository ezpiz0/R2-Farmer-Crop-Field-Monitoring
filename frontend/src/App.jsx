import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { ThemeProvider } from './contexts/ThemeContext'
import AuthPage from './components/AuthPage'
import HomePage from './components/HomePage'
import MapPage from './components/MapPage'
import DashboardPage from './components/DashboardPage'
import ProfilePage from './components/ProfilePage'
import './App.css'

function AppContent() {
  const { isAuthenticated } = useAuth()

  return (
    <>
      <Routes>
        {/* Auth page route */}
        <Route 
          path="/auth" 
          element={isAuthenticated ? <Navigate to="/" /> : <AuthPage />} 
        />
        
        {/* Home page - protected */}
        <Route 
          path="/" 
          element={isAuthenticated ? <HomePage /> : <Navigate to="/auth" />} 
        />
        
        {/* Map page - protected */}
        <Route 
          path="/map" 
          element={isAuthenticated ? <MapPage /> : <Navigate to="/auth" />} 
        />
        
        {/* Dashboard page - protected */}
        <Route 
          path="/dashboard" 
          element={isAuthenticated ? <DashboardPage /> : <Navigate to="/auth" />} 
        />
        
        {/* Profile page - protected */}
        <Route 
          path="/profile" 
          element={isAuthenticated ? <ProfilePage /> : <Navigate to="/auth" />} 
        />
      </Routes>
    </>
  )
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Router>
          <AppContent />
        </Router>
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App



