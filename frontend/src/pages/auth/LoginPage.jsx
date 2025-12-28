import React from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import CenteredPageLayout from '../../components/layout/CenteredPageLayout';
import Card from '../../components/common/Card';
import './LoginPage.css';

export default function LoginPage() {
  const { handleGoogleSuccess } = useAuth();
  const navigate = useNavigate();

  const onSuccess = async (credentialResponse) => {
    try {
      await handleGoogleSuccess(credentialResponse);
      navigate('/');
    } catch (error) {
      console.error('Login failed:', error);
      alert('Login failed. Please try again.');
    }
  };

  const onError = () => {
    console.error('Google login failed');
    alert('Google login failed. Please try again.');
  };

  return (
    <CenteredPageLayout>
      <Card title="ChainLines" subtitle="Sign in to contribute to the timeline">
        <div className="login-button-wrapper">
          <GoogleLogin
            onSuccess={onSuccess}
            onError={onError}
            useOneTap
          />
        </div>

        <div className="login-info">
          <h3>Why sign in?</h3>
          <ul>
            <li>Edit team information</li>
            <li>Create lineage events</li>
            <li>Contribute to cycling history</li>
          </ul>
        </div>
      </Card>
    </CenteredPageLayout>
  );
}
