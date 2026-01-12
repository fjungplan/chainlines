import React from 'react';
import './Loading.css';

const CHAIN_PATH_D = "M 180 22 L 60 22 A 18 18 0 0 0 60 58 L 72 64 A 6 6 0 0 1 72 76 L 52 90 A 6 6 0 0 0 52 102 L 180 98 A 38 38 0 1 0 180 22";

const CHAIN_COLORS = [
    '#FE2B1A', // Vuelta Red
    '#FF286E', // Giro Pink
    '#FFFF00', // Tour Yellow
    '#00BF4F', // Points Green
    '#0E62FE', // Azzurra Blue
];

const DrivetrainSpinner = () => {
    // Use stroke-dasharray to simulate teeth on gears
    // Chain path approximates a loop around the two gears
    return (
        <svg
            className="drivetrain-spinner"
            viewBox="0 0 240 140"
            xmlns="http://www.w3.org/2000/svg"
        >
            <defs>
                {/* No gradient needed for multi-color path */}
            </defs>

            {/* Derailleur Arm & Pulleys (Rear Mech) */}
            <g className="derailleur" transform="translate(60, 40)">
                {/* Cage Arm - Shortened: (12,30) to (-8,56) */}
                <path
                    d="M 12 30 L -8 56"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    opacity="0.8"
                />

                {/* Upper Pulley (Guide) - Wrapped for stable rotation */}
                <g transform="translate(12, 30)">
                    <circle cx="0" cy="0" r="6" fill="none" stroke="currentColor" strokeWidth="2" className="pulley upper-pulley" />
                </g>

                {/* Lower Pulley (Tension) - Wrapped & Moved closer (-8, 56) */}
                <g transform="translate(-8, 56)">
                    <circle cx="0" cy="0" r="6" fill="none" stroke="currentColor" strokeWidth="2" className="pulley lower-pulley" />
                </g>
            </g>

            {/* The Chain - Multi-colored Segments */}
            {CHAIN_COLORS.map((color, index) => (
                <path
                    key={color}
                    className="chain"
                    d={CHAIN_PATH_D}
                    fill="none"
                    stroke={color}
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeDasharray="10 60" // 10px link, 60px gap to next color (Total 70px)
                    style={{
                        '--start-offset': `${-14 * index}px`,
                        // Ensure animation uses this variable
                    }}
                />
            ))}

            {/* Cassette (Rear Gear) - Moved up to Y=40 */}
            <g transform="translate(60, 40)">
                <g className="cassette">
                    {/* Cog Body */}
                    <circle cx="0" cy="0" r="18" fill="var(--color-bg-primary)" stroke="currentColor" strokeWidth="6" strokeDasharray="5 3" />
                    <circle cx="0" cy="0" r="6" fill="currentColor" />
                </g>
            </g>

            {/* Chainring (Front Gear) */}
            <g transform="translate(180, 60)">
                <g className="chainring">
                    {/* Cog Body */}
                    <circle cx="0" cy="0" r="38" fill="var(--color-bg-primary)" stroke="currentColor" strokeWidth="6" strokeDasharray="8 6" />

                    {/* Crank Arm (Visualizes rotation better) */}
                    <rect x="-10" y="-8" width="82" height="16" rx="8" fill="currentColor" className="crank-arm" />
                    <circle cx="0" cy="0" r="10" fill="var(--color-bg-primary)" stroke="currentColor" strokeWidth="2" />
                </g>
            </g>
        </svg>
    );
}

export default DrivetrainSpinner;
