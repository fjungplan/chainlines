import { BrowserRouter, Routes, Route } from 'react-router-dom';
import MainLayout from './components/layout/MainLayout';
import HomePage from './pages/HomePage';
import TeamDetailPage from './pages/TeamDetailPage';
import LoginPage from './pages/auth/LoginPage';
import NotFoundPage from './pages/NotFoundPage';

import AuditLogPage from './pages/AuditLogPage';
import AuditLogEditor from './pages/AuditLogEditor';
import MyEditsPage from './pages/MyEditsPage';
import AdminPanelPage from './pages/AdminPanelPage';
import SponsorMaintenancePage from './pages/maintenance/SponsorMaintenancePage';
import TeamMaintenancePage from './pages/maintenance/TeamMaintenancePage';
import LineageMaintenancePage from './pages/maintenance/LineageMaintenancePage';
import UserMaintenancePage from './pages/maintenance/UserMaintenancePage';
import AboutPage from './pages/AboutPage';
import ImprintPage from './pages/ImprintPage';
import { ErrorBoundary } from './components/ErrorDisplay';

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<HomePage />} />
            <Route path="team/:nodeId" element={<TeamDetailPage />} />
            <Route path="login" element={<LoginPage />} />
            <Route path="about" element={<AboutPage />} />
            <Route path="imprint" element={<ImprintPage />} />

            <Route path="audit-log" element={<AuditLogPage />} />
            <Route path="audit-log/:editId" element={<AuditLogEditor />} />
            <Route path="me/edits" element={<MyEditsPage />} />
            <Route path="admin" element={<AdminPanelPage />} />
            <Route path="maintenance/sponsors" element={<SponsorMaintenancePage />} />
            <Route path="maintenance/teams" element={<TeamMaintenancePage />} />
            <Route path="maintenance/lineage" element={<LineageMaintenancePage />} />
            <Route path="admin/users" element={<UserMaintenancePage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
