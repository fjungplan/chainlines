import { useAuth } from '../contexts/AuthContext';

export default function AdminPanelPage() {
  const { isAdmin } = useAuth();

  if (!isAdmin()) {
    return <p style={{ padding: '1rem' }}>Admin access required.</p>;
  }

  return (
    <div style={{ padding: '1rem' }}>
      <h2>Admin Panel</h2>
      <p>Admin utilities will go here.</p>
    </div>
  );
}
