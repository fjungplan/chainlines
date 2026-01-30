import React from 'react';
import { Link } from 'react-router-dom';
import '../components/layout/CenteredPageContainer.css';
import '../components/layout/CenteredContentCard.css';

export default function OptimizerSettings() {
    return (
        <div className="centered-page-container">
            <div className="centered-content-card">
                <div className="card-header">
                    <div className="header-left">
                        <Link to="/admin/optimizer" className="back-link" title="Back to Optimizer">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M20 11H7.83L13.42 5.41L12 4L4 12L12 20L13.41 18.59L7.83 13H20V11Z" fill="currentColor" />
                            </svg>
                        </Link>
                        <h1>Optimizer Settings</h1>
                    </div>
                </div>
                <div className="card-content">
                    <p style={{ color: 'var(--text-secondary)' }}>
                        Settings form coming soon...
                    </p>
                </div>
            </div>
        </div>
    );
}
