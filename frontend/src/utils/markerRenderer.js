
import * as d3 from 'd3';
import { VISUALIZATION } from '../constants/visualization';
import { TooltipBuilder } from './tooltipBuilder'; // Assuming import path

export class MarkerRenderer {
    static getMarkerDimensions(layout) {
        const nodeHeight = layout?.nodeHeight || VISUALIZATION.NODE_HEIGHT;

        const lineHeight = nodeHeight * 0.9;
        const radius = Math.max(3.5, nodeHeight * 0.12);
        const strokeWidth = Math.max(2, nodeHeight * 0.08);

        return {
            lineHeight,
            halfHeight: lineHeight / 2,
            radius,
            strokeWidth
        };
    }

    static render(g, links, layout, setTooltip) {
        // Only render markers for same-swimlane transitions
        const markerData = links.filter(d => d.sameSwimlane && d.path === null);

        let markerGroup = g.select('.transition-markers');
        if (markerGroup.empty()) {
            markerGroup = g.append('g').attr('class', 'transition-markers');
        }

        const { halfHeight, radius, strokeWidth } = this.getMarkerDimensions(layout);

        const markers = markerGroup
            .selectAll('g.transition-marker')
            .data(markerData, (d) => `marker-${d.source}-${d.target}-${d.year || ''}`)
            .join('g')
            .attr('class', 'transition-marker')
            .style('cursor', 'pointer')
            .on('mouseenter', (event, d) => {
                d3.select(event.currentTarget).select('line').attr('stroke-width', strokeWidth * 1.5);
                d3.select(event.currentTarget).select('circle').attr('r', radius * 1.5);

                // We need nodes for tooltip, assuming they are in layout
                const content = TooltipBuilder.buildLinkTooltip(d, layout?.nodes || []);
                if (content) {
                    setTooltip({ visible: true, content, position: { x: event.pageX, y: event.pageY } });
                }
            })
            .on('mousemove', (event) => {
                // This needs to be handled by the parent or passed down callback, 
                // but for now we follow the existing pattern if setTooltip supports updates
                // Actually, the original code had setTooltip(prev => ...)
                // We'll assume setTooltip handles the update logic or we pass a wrapper.
                // For the refactor, let's keep it simple: assume parent passes a simple setter
                // If we need the "prev" logic, we rely on the component.
                // However, React state setters can take a function.
                setTooltip(prev => ({ ...prev, position: { x: event.pageX, y: event.pageY } }));
            })
            .on('mouseleave', (event) => {
                d3.select(event.currentTarget).select('line').attr('stroke-width', strokeWidth);
                d3.select(event.currentTarget).select('circle').attr('r', radius);
                setTooltip({ visible: false, content: null, position: null });
            });

        // Vertical line marker
        markers
            .selectAll('line')
            .data(d => [d])
            .join('line')
            .attr('x1', (d) => d.targetX)
            .attr('y1', (d) => d.targetY - halfHeight)
            .attr('x2', (d) => d.targetX)
            .attr('y2', (d) => d.targetY + halfHeight)
            .attr('stroke', (d) =>
                d.type === 'SPIRITUAL_SUCCESSION' ? VISUALIZATION.LINK_COLOR_SPIRITUAL : VISUALIZATION.LINK_COLOR_LEGAL
            )
            .attr('stroke-width', strokeWidth)
            .attr('stroke-dasharray', (d) => (d.type === 'SPIRITUAL_SUCCESSION' ? '4,2' : '0'));

        // Circle at center
        markers
            .selectAll('circle')
            .data(d => [d])
            .join('circle')
            .attr('cx', (d) => d.targetX)
            .attr('cy', (d) => d.targetY)
            .attr('r', radius)
            .attr('fill', (d) =>
                d.type === 'SPIRITUAL_SUCCESSION' ? VISUALIZATION.LINK_COLOR_SPIRITUAL : VISUALIZATION.LINK_COLOR_LEGAL
            )
            .attr('stroke', '#fff')
            .attr('stroke-width', Math.max(1, strokeWidth * 0.5));
    }
}
