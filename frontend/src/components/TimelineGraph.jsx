import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import './TimelineGraph.css';

export default function TimelineGraph({ data }) {
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  
  useEffect(() => {
    if (!data || !data.nodes || !data.links) return;
    
    // Clear previous render
    d3.select(svgRef.current).selectAll('*').remove();
    
    // Initialize visualization
    initializeVisualization();
  }, [data]);
  
  const initializeVisualization = () => {
    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    // Create SVG
    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', [0, 0, width, height]);
    
    // Add zoom behavior
    const g = svg.append('g');
    
    const zoom = d3.zoom()
      .scaleExtent([0.5, 5])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });
    
    svg.call(zoom);
    
    // For now, just render placeholder
    g.append('text')
      .attr('x', width / 2)
      .attr('y', height / 2)
      .attr('text-anchor', 'middle')
      .attr('font-size', '24px')
      .attr('fill', '#333')
      .text('D3 Graph Container Ready');
  };
  
  return (
    <div 
      ref={containerRef} 
      className="timeline-graph-container"
    >
      <svg ref={svgRef}></svg>
    </div>
  );
}
