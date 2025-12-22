import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import TeamDetailPage from './pages/TeamDetailPage';
import LoginPage from './pages/LoginPage';
import NotFoundPage from './pages/NotFoundPage';
import ModerationQueuePage from './pages/ModerationQueuePage';
import MyEditsPage from './pages/MyEditsPage';
import AdminPanelPage from './pages/AdminPanelPage';
import SponsorMaintenancePage from './pages/SponsorMaintenancePage';
import TeamMaintenancePage from './pages/TeamMaintenancePage';
import AboutPage from './pages/AboutPage';
import ImprintPage from './pages/ImprintPage';
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
            <Route path="about" element={<AboutPage />} />
            <Route path="imprint" element={<ImprintPage />} />
            <Route path="moderation" element={<ModerationQueuePage />} />
            <Route path="me/edits" element={<MyEditsPage />} />
            <Route path="admin" element={<AdminPanelPage />} />
            <Route path="maintenance/sponsors" element={<SponsorMaintenancePage />} />
            <Route path="maintenance/teams" element={<TeamMaintenancePage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
