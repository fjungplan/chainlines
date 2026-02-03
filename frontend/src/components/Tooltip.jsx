import React, { useEffect, useRef } from 'react';
import './Tooltip.css';

export default function Tooltip({ content, position, visible }) {
  const tooltipRef = useRef(null);

  useEffect(() => {
    if (visible && tooltipRef.current && position) {
      const tooltip = tooltipRef.current;
      const rect = tooltip.getBoundingClientRect();

      const offset = 15;
      const padding = 10;

      // Default: Bottom-Right (as requested)
      let x = position.x + offset;
      let y = position.y + offset;

      // Flip Right -> Left if it overflows
      if (x + rect.width > window.innerWidth - padding) {
        x = position.x - rect.width - offset;
      }

      // Flip Bottom -> Top if it overflows
      if (y + rect.height > window.innerHeight - padding) {
        y = position.y - rect.height - offset;
      }

      // Safety: clamp to screen if STILL overflowing
      x = Math.max(padding, Math.min(x, window.innerWidth - rect.width - padding));
      y = Math.max(padding, Math.min(y, window.innerHeight - rect.height - padding));

      tooltip.style.left = `${x}px`;
      tooltip.style.top = `${y}px`;
    }
  }, [position, visible]);

  if (!visible || !content) return null;

  return (
    <div ref={tooltipRef} className="timeline-tooltip">
      {content}
    </div>
  );
}
