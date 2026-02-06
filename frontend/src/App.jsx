import { BrowserRouter, Routes, Route } from 'react-router-dom';
import MainLayout from './components/layout/MainLayout';
import HomePage from './pages/HomePage';
import TeamDetailPage from './pages/TeamDetailPage';
import LoginPage from './pages/auth/LoginPage';
import NotFoundPage from './pages/NotFoundPage';

import AuditLogPage from './pages/AuditLogPage';
import AuditLogEditor from './pages/AuditLogEditor';
import MyEditsPage from './pages/MyEditsPage';
import { auditLogApi } from './api/auditLog';
import AdminPanelPage from './pages/AdminPanelPage';
import SponsorMaintenancePage from './pages/maintenance/SponsorMaintenancePage';
import TeamMaintenancePage from './pages/maintenance/TeamMaintenancePage';
import LineageMaintenancePage from './pages/maintenance/LineageMaintenancePage';
import ScraperMaintenancePage from './pages/maintenance/ScraperMaintenancePage';
import UserMaintenancePage from './pages/maintenance/UserMaintenancePage';
import AdminOptimizer from './pages/AdminOptimizer';
import OptimizerSettings from './pages/OptimizerSettings';
import AboutPage from './pages/AboutPage';
import ImprintPage from './pages/ImprintPage';
import ChangeLogPage from './pages/ChangeLogPage';
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
            <Route path="changelog" element={<ChangeLogPage />} />

            <Route path="audit-log" element={<AuditLogPage />} />
            <Route path="audit-log/:editId" element={<AuditLogEditor />} />
            <Route path="me/edits" element={<MyEditsPage />} />
            <Route path="me/edits/:editId" element={<AuditLogEditor backPath="/me/edits" apiMethod={auditLogApi.getMyDetail} />} />
            <Route path="admin" element={<AdminPanelPage />} />
            <Route path="maintenance/sponsors" element={<SponsorMaintenancePage />} />
            <Route path="maintenance/teams" element={<TeamMaintenancePage />} />
            <Route path="maintenance/lineage" element={<LineageMaintenancePage />} />
            <Route path="admin/scraper" element={<ScraperMaintenancePage />} />
            <Route path="admin/users" element={<UserMaintenancePage />} />
            <Route path="admin/optimizer" element={<AdminOptimizer />} />
            <Route path="admin/optimizer/settings" element={<OptimizerSettings />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
