import { useEffect, useState } from 'react';
import { editsApi } from '../api/edits';
import { useAuth } from '../contexts/AuthContext';

export default function MyEditsPage() {
  const { isAuthenticated } = useAuth();
  const [edits, setEdits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isAuthenticated) {
      setLoading(false);
      setError('Please sign in to view your edits.');
      return;
    }
    const fetchEdits = async () => {
      try {
        const res = await editsApi.getMyEdits();
        setEdits(res.data || []);
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load edits');
      } finally {
        setLoading(false);
      }
    };
    fetchEdits();
  }, [isAuthenticated]);

  if (loading) return <p>Loading…</p>;
  if (error) return <p>{error}</p>;

  return (
    <div style={{ padding: '1rem' }}>
      <h2>My Edits</h2>
      {edits.length === 0 ? (
        <p>No edits yet.</p>
      ) : (
        <ul>
          {edits.map((edit) => (
            <li key={edit.edit_id}>
              <strong>{edit.edit_type}</strong> – {edit.status}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
