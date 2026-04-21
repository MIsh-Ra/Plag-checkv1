import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ReportView from './pages/ReportView';
import AdminPanel from './pages/AdminPanel';
import GlobalLayout from './components/layout/GlobalLayout';
import { ThemeProvider } from './components/ThemeContext';
import './App.css';

function ProtectedRoute({ children }) {
    const token = localStorage.getItem('alethian_token');
    if (!token) return <Navigate to="/login" replace />;
    return <GlobalLayout>{children}</GlobalLayout>;
}

function App() {
  return (
    <ThemeProvider>
      <Router>
        <div className="min-h-screen bg-background text-on-background font-sans">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/report/:id" element={<ProtectedRoute><ReportView /></ProtectedRoute>} />
            <Route path="/admin" element={<ProtectedRoute><AdminPanel /></ProtectedRoute>} />

            {/* Default Redirect */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;
