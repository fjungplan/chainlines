import React, { useState, useEffect } from 'react';
import './ResolutionBlocker.css'; // We'll create a basic CSS file for this

/**
 * Blocking screen for resolutions that fit too few decades
 * Requires roughly 60px per decade label to ensure readability at Overview zoom
 */
export function ResolutionBlocker({ startYear, endYear, children }) {
    const [isBlocked, setIsBlocked] = useState(false);
    const [minWidth, setMinWidth] = useState(0);
    const [currentWidth, setCurrentWidth] = useState(window.innerWidth);

    useEffect(() => {
        const checkResolution = () => {
            const width = window.innerWidth;
            setCurrentWidth(width);

            // Standard tablet portrait breakpoint
            const MIN_WIDTH = 768;
            setMinWidth(MIN_WIDTH);

            // Block if screen is narrower than standard breakpoint
            setIsBlocked(width < MIN_WIDTH);
        };

        checkResolution();
        window.addEventListener('resize', checkResolution);
        return () => window.removeEventListener('resize', checkResolution);
    }, []);

    if (isBlocked) {
        return (
            <div className="resolution-blocker">
                <div className="blocker-content">
                    <h2>Screen Resolution Too Low</h2>
                    <p>
                        The detailed timeline requires a wider screen to display properly.
                    </p>
                    <div className="metrics">
                        <p><strong>Required Width:</strong> {minWidth}px</p>
                        <p><strong>Current Width:</strong> {currentWidth}px</p>
                    </div>
                    <p className="hint">
                        Please maximize your window or switch to a desktop device.
                    </p>
                </div>
            </div>
        );
    }

    return children;
}
