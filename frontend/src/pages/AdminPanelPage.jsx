import { useAuth } from '../contexts/AuthContext';
import CenteredPageLayout from '../components/layout/CenteredPageLayout';
import Card from '../components/common/Card';

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
        <p>Admin utilities will go here.</p>
      </Card>
    </CenteredPageLayout>
  );
}
