import React, { useState, useEffect } from 'react';
import './NavigationHint.css';

const NavigationHint = ({ duration = 5000 }) => {
    const [isVisible, setIsVisible] = useState(true);

    useEffect(() => {
        const timer = setTimeout(() => {
            setIsVisible(false);
        }, duration);

        return () => clearTimeout(timer);
    }, [duration]);

    if (!isVisible) return null;

    return (
        <div
            className="navigation-hint-overlay"
            onClick={() => setIsVisible(false)}
            role="presentation"
        >
            <div className="navigation-hint-content">
                <div className="hint-item">
                    <span>Left/Middle Click + Drag to Pan</span>
                </div>
                <div className="hint-item">
                    <span>Scroll to Move Vertically</span>
                </div>
                <div className="hint-item">
                    <span>Ctrl + Scroll to Zoom</span>
                </div>
            </div>
        </div>
    );
};

export default NavigationHint;
