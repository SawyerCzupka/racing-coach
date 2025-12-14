import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './providers/theme-provider';
import { QueryProvider } from './providers/query-provider';
import { AuthProvider } from './providers/auth-provider';
import { RootLayout } from './components/layout/root-layout';
import { AuthLayout } from './components/auth/auth-layout';
import { ProtectedRoute } from './components/auth/protected-route';
import { LandingPage } from './pages/landing-page';
import { LoginPage } from './pages/login-page';
import { RegisterPage } from './pages/register-page';
import { SessionsPage } from './pages/sessions-page';
import { SessionDetailPage } from './pages/session-detail-page';
import { LapDetailPage } from './pages/lap-detail-page';
import { ComparePage } from './pages/compare-page';
import { LivePage } from './pages/live-page';

function App() {
  return (
    <ThemeProvider defaultTheme="dark">
      <QueryProvider>
        <BrowserRouter>
          <AuthProvider>
            <Routes>
              {/* Public routes */}
              <Route path="/" element={<LandingPage />} />
              <Route element={<AuthLayout />}>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
              </Route>

              {/* Protected routes */}
              <Route
                element={
                  <ProtectedRoute>
                    <RootLayout />
                  </ProtectedRoute>
                }
              >
                <Route path="/sessions" element={<SessionsPage />} />
                <Route path="/session/:sessionId" element={<SessionDetailPage />} />
                <Route path="/lap/:lapId" element={<LapDetailPage />} />
                <Route path="/compare" element={<ComparePage />} />
                <Route path="/live" element={<LivePage />} />
              </Route>
            </Routes>
          </AuthProvider>
        </BrowserRouter>
      </QueryProvider>
    </ThemeProvider>
  );
}

export default App;
