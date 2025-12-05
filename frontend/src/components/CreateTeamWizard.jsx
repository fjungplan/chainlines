import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { editsApi } from '../api/edits';
import './CreateTeamWizard.css';

export default function CreateTeamWizard({ onClose, onSuccess }) {
  const { user } = useAuth();
  const currentYear = new Date().getFullYear();
  
  const [formData, setFormData] = useState({
    registered_name: '',
    founding_year: currentYear,
    uci_code: '',
    tier_level: '2',
    reason: ''
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  
  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError(null);
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    
    try {
      // Validate required fields
      if (!formData.registered_name || formData.registered_name.trim().length === 0) {
        setError('Team name is required');
        setSubmitting(false);
        return;
      }
      
      if (!formData.founding_year) {
        setError('Founding year is required');
        setSubmitting(false);
        return;
      }
      
      if (!formData.tier_level) {
        setError('Tier level is required');
        setSubmitting(false);
        return;
      }
      
      if (!formData.reason || formData.reason.length < 10) {
        setError('Reason must be at least 10 characters');
        setSubmitting(false);
        return;
      }
      
      // Send request to create team (uses EditService behind the scenes)
      const response = await editsApi.createTeam({
        registered_name: formData.registered_name,
        founding_year: parseInt(formData.founding_year),
        uci_code: formData.uci_code || null,
        tier_level: parseInt(formData.tier_level),
        reason: formData.reason
      });
      
      onSuccess(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create team');
    } finally {
      setSubmitting(false);
    }
  };
  
  return (
    <div className="wizard-overlay" onClick={onClose}>
      <div className="wizard-modal" onClick={(e) => e.stopPropagation()}>
        <div className="wizard-header">
          <h2>Create New Team</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="form-section">
            <label>
              Team Name *
              <input
                type="text"
                value={formData.registered_name}
                onChange={(e) => handleChange('registered_name', e.target.value)}
                placeholder="e.g., Team Sky, Ineos Grenadiers"
                required
              />
            </label>
            
            <label>
              Founding Year *
              <input
                type="number"
                value={formData.founding_year}
                onChange={(e) => handleChange('founding_year', e.target.value)}
                min="1900"
                max="2100"
                required
              />
            </label>
            
            <label>
              UCI Code (3 letters)
              <input
                type="text"
                value={formData.uci_code}
                onChange={(e) => handleChange('uci_code', e.target.value.toUpperCase())}
                maxLength={3}
                pattern="[A-Z]{3}"
                placeholder="Optional"
              />
            </label>
            
            <label>
              Initial Tier Level *
              <select
                value={formData.tier_level}
                onChange={(e) => handleChange('tier_level', e.target.value)}
                required
              >
                <option value="">Select tier...</option>
                <option value="1">UCI WorldTour</option>
                <option value="2">UCI ProTeam</option>
                <option value="3">UCI Continental</option>
              </select>
            </label>
          </div>
          
          <div className="form-section">
            <label>
              Reason for Creation (required) *
              <textarea
                value={formData.reason}
                onChange={(e) => handleChange('reason', e.target.value)}
                placeholder="Explain why this team is being added to the system..."
                rows={4}
                required
                minLength={10}
              />
            </label>
            <div className="help-text">
              Please provide context: Is this a team that existed historically but wasn't in the system? 
              Is this a newly formed team? Include sources if available.
            </div>
          </div>
          
          {error && (
            <div className="error-message">{error}</div>
          )}
          
          <div className="wizard-footer">
            <div className="moderation-notice">
              {user?.role === 'NEW_USER' ? (
                <span className="notice-warning">
                  ⚠️ This team creation will be reviewed by moderators
                </span>
              ) : (
                <span className="notice-success">
                  ✓ This team will be created immediately
                </span>
              )}
            </div>
            
            <div className="button-group">
              <button 
                type="button" 
                onClick={onClose}
                disabled={submitting}
              >
                Cancel
              </button>
              <button 
                type="submit"
                disabled={submitting || !formData.registered_name || !formData.reason || formData.reason.length < 10}
                className="primary"
              >
                {submitting ? 'Creating...' : 'Create Team'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
