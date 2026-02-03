import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import CenteredPageLayout from '../components/layout/CenteredPageLayout';
import Card from '../components/common/Card';
import '../components/common/Button.css';

export default function AdminPanelPage() {
  const { isAdmin } = useAuth();

  if (!isAdmin()) {
    return (
      <CenteredPageLayout>
        <Card title="Access Denied">
          <p>Admin access required.</p>
        </Card>
      </CenteredPageLayout>
    );
  }

  return (
    <CenteredPageLayout>
      <Card title="Admin Panel">
        <div className="admin-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
          <Link to="/admin/users" className="btn btn-tile">
            <span className="tile-icon"><i className="bi bi-people"></i></span>
            <div className="tile-content">
              <h3>User Maintenance</h3>
              <p>Manage users, roles, and bans.</p>
            </div>
          </Link>

          <Link to="/admin/scraper" className="btn btn-tile">
            <span className="tile-icon"><i className="bi bi-arrow-repeat"></i></span>
            <div className="tile-content">
              <h3>Scraper Status</h3>
              <p>Scraper execution and logs.</p>
            </div>
          </Link>

          <Link to="/admin/optimizer" className="btn btn-tile">
            <span className="tile-icon"><i className="bi bi-cpu"></i></span>
            <div className="tile-content">
              <h3>Layout Optimizer</h3>
              <p>Optimize complex family layouts.</p>
            </div>
          </Link>
        </div>
      </Card>
    </CenteredPageLayout>
  );
}
