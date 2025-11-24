import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './providers/theme-provider';
import { QueryProvider } from './providers/query-provider';
import { RootLayout } from './components/layout/root-layout';
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
          <Routes>
            <Route element={<RootLayout />}>
              <Route index element={<SessionsPage />} />
              <Route path="/session/:sessionId" element={<SessionDetailPage />} />
              <Route path="/lap/:lapId" element={<LapDetailPage />} />
              <Route path="/compare" element={<ComparePage />} />
              <Route path="/live" element={<LivePage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </QueryProvider>
    </ThemeProvider>
  );
}

export default App;
