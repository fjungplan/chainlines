import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import TeamDetailPage from './pages/TeamDetailPage';
import LoginPage from './pages/LoginPage';
import NotFoundPage from './pages/NotFoundPage';
import ModerationQueuePage from './pages/ModerationQueuePage';
import { ErrorBoundary } from './components/ErrorDisplay';

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<HomePage />} />
            <Route path="team/:nodeId" element={<TeamDetailPage />} />
            <Route path="login" element={<LoginPage />} />
            <Route path="moderation" element={<ModerationQueuePage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
