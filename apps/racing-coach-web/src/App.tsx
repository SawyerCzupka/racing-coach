import { BrowserRouter, Route, Routes } from 'react-router';
import { AuthLayout } from './components/auth/auth-layout';
import { ProtectedRoute } from './components/auth/protected-route';
import { RootLayout } from './components/layout/root-layout';
import { ComparePage } from './pages/compare-page';
import { CornerSegmentEditorPage } from './pages/corner-segment-editor-page';
import { DashboardPage } from './pages/dashboard-page';
import { DeviceAuthPage } from './pages/device-auth-page';
import { LandingPage } from './pages/landing-page';
import { LapDetailPage } from './pages/lap-detail-page';
import { LivePage } from './pages/live-page';
import { LoginPage } from './pages/login-page';
import { RegisterPage } from './pages/register-page';
import { SessionDetailPage } from './pages/session-detail-page';
import { SessionsPage } from './pages/sessions-page';
import { TrackBoundariesPage } from './pages/track-boundaries-page';
import { TrackBoundaryDetailPage } from './pages/track-boundary-detail-page';
import { TrackBoundaryUploadPage } from './pages/track-boundary-upload-page';
import { AuthProvider } from './providers/auth-provider';
import { QueryProvider } from './providers/query-provider';
import { ThemeProvider } from './providers/theme-provider';

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

              {/* Device authorization (requires auth, uses simple layout) */}
              <Route
                path="/auth/device"
                element={
                  <ProtectedRoute>
                    <AuthLayout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<DeviceAuthPage />} />
              </Route>

              {/* Protected routes */}
              <Route
                element={
                  <ProtectedRoute>
                    <RootLayout />
                  </ProtectedRoute>
                }
              >
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/sessions" element={<SessionsPage />} />
                <Route path="/session/:sessionId" element={<SessionDetailPage />} />
                <Route path="/lap/:lapId" element={<LapDetailPage />} />
                <Route path="/compare" element={<ComparePage />} />
                <Route path="/live" element={<LivePage />} />
              </Route>

              {/* Admin-only routes */}
              <Route
                element={
                  <ProtectedRoute requireAdmin>
                    <RootLayout />
                  </ProtectedRoute>
                }
              >
                <Route path="/tracks" element={<TrackBoundariesPage />} />
                <Route path="/tracks/upload" element={<TrackBoundaryUploadPage />} />
                <Route path="/tracks/:boundaryId" element={<TrackBoundaryDetailPage />} />
                <Route path="/tracks/:boundaryId/corners" element={<CornerSegmentEditorPage />} />
              </Route>
            </Routes>
          </AuthProvider>
        </BrowserRouter>
      </QueryProvider>
    </ThemeProvider>
  );
}

export default App;
