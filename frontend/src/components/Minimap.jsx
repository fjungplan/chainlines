import React, { useRef, useEffect, useState } from 'react';
import * as d3 from 'd3';
import './Minimap.css';

export default function Minimap({ layout, mainLayout, transform, containerDimensions, onNavigate }) {
    const svgRef = useRef(null);
    const viewportRef = useRef(null);
    const containerRef = useRef(null);
    const transformRef = useRef(transform);
    const mainLayoutRef = useRef(mainLayout);
    const containerDimensionsRef = useRef(containerDimensions);
    const scaleXRef = useRef(1);
    const scaleYRef = useRef(1);
    const layoutDataRef = useRef(null);
    const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

    // Update refs whenever props change
    useEffect(() => {
        transformRef.current = transform;
    }, [transform]);

    useEffect(() => {
        mainLayoutRef.current = mainLayout;
    }, [mainLayout]);

    useEffect(() => {
        containerDimensionsRef.current = containerDimensions;
    }, [containerDimensions]);

    useEffect(() => {
        if (!containerRef.current) return;

        const measure = () => {
            if (containerRef.current) {
                setDimensions({
                    width: containerRef.current.clientWidth,
                    height: containerRef.current.clientHeight
                });
            }
        };

        measure();
        const resizeObserver = new ResizeObserver(measure);
        resizeObserver.observe(containerRef.current);
        return () => resizeObserver.disconnect();
    }, []);

    // Setup drag behavior ONCE on mount
    useEffect(() => {
        if (!viewportRef.current || !svgRef.current) return;

        const viewport = d3.select(viewportRef.current);
        let dragStartState = null;

        const drag = d3.drag()
            .on('start', function (event) {
                d3.select(this).classed('dragging', true);
                const startPtr = d3.pointer(event.sourceEvent, svgRef.current);

                const currentTransform = transformRef.current;
                dragStartState = {
                    ptrX: startPtr[0],
                    ptrY: startPtr[1],
                    transformX: currentTransform.x,
                    transformY: currentTransform.y,
                    transformK: currentTransform.k
                };
            })
            .on('drag', function (event) {
                const mainLayout = mainLayoutRef.current;
                const layoutData = layoutDataRef.current;

                if (!mainLayout || !dragStartState || !layoutData) return;

                const currentPtr = d3.pointer(event.sourceEvent, svgRef.current);
                const dxScreen = currentPtr[0] - dragStartState.ptrX;
                const dyScreen = currentPtr[1] - dragStartState.ptrY;

                // Convert screen delta to minimap world delta
                const dxMiniWorld = dxScreen / scaleXRef.current;
                const dyMiniWorld = dyScreen / scaleYRef.current;

                // X: Convert minimap world delta to YEARS, then years to main world delta
                const { yearRange, xScale, miniMinY, miniMaxY, mainBounds } = layoutData;
                const miniMinYear = yearRange.min;
                const miniMaxYear = yearRange.max;
                const miniXStart = xScale(miniMinYear);
                const miniXEnd = xScale(miniMaxYear);
                const miniPixelsPerYear = (miniXEnd - miniXStart) / ((miniMaxYear - miniMinYear) || 1);

                const deltaYears = dxMiniWorld / miniPixelsPerYear;

                const mainMinYear = mainLayout.yearRange.min;
                const mainMaxYear = mainLayout.yearRange.max;
                const mainXStart = mainLayout.xScale(mainMinYear);
                const mainXEnd = mainLayout.xScale(mainMaxYear);
                const mainPixelsPerYear = (mainXEnd - mainXStart) / ((mainMaxYear - mainMinYear) || 1);

                const dxMainWorld = deltaYears * mainPixelsPerYear;

                // Y: Use ratio
                const miniContentHeight = miniMaxY - miniMinY;
                const mainContentHeight = mainBounds.maxY - mainBounds.minY;
                const yRatio = mainContentHeight / miniContentHeight;
                const dyMainWorld = dyMiniWorld * yRatio;

                // Apply delta to starting transform
                let newTransformX = dragStartState.transformX - dxMainWorld * dragStartState.transformK;
                let newTransformY = dragStartState.transformY - dyMainWorld * dragStartState.transformK;

                // Clamp transform to respect the main timeline's extent bounds
                // The extent defines the world coordinates that can be panned to
                const containerDims = containerDimensionsRef.current;
                if (containerDims && mainBounds) {
                    const k = dragStartState.transformK;

                    // Calculate the extent in world coordinates (same as in TimelineGraph zoom setup)
                    const yearMin = mainLayout.xScale(mainLayout.yearRange.min);
                    const yearMax = mainLayout.xScale(mainLayout.yearRange.max);
                    const paddedMinY = mainBounds.minY - 50; // VERTICAL_PADDING
                    const paddedMaxY = mainBounds.maxY + 50;

                    // Transform bounds: prevent panning beyond extent
                    // translateExtent [[x0, y0], [x1, y1]] means top-left corner can pan from x0,y0 to x1,y1
                    // In screen coords: -transform.x/k should stay within [x0, x1]
                    // So: transform.x should stay within [-x1*k, -x0*k]
                    const minTransformX = -(yearMax * k - containerDims.width);
                    const maxTransformX = -yearMin * k;
                    const minTransformY = -(paddedMaxY * k - containerDims.height);
                    const maxTransformY = -paddedMinY * k;

                    newTransformX = Math.max(minTransformX, Math.min(maxTransformX, newTransformX));
                    newTransformY = Math.max(minTransformY, Math.min(maxTransformY, newTransformY));
                }

                if (onNavigate) {
                    const newTransform = d3.zoomIdentity
                        .translate(newTransformX, newTransformY)
                        .scale(dragStartState.transformK);
                    onNavigate(newTransform);
                }
            })
            .on('end', function () {
                d3.select(this).classed('dragging', false);
                dragStartState = null;
            });

        viewport.call(drag);

        // Cleanup: remove drag behavior on unmount
        return () => {
            viewport.on('.drag', null);
        };
    }, []); // Only run once on mount

    // Update viewport position and nodes (but NOT drag behavior)
    useEffect(() => {
        const { width, height } = dimensions;
        if (!layout || !containerDimensions || width === 0 || height === 0) return;

        const nodes = layout.nodes || [];
        if (nodes.length === 0) return;

        const xScale = layout.xScale;
        const yearRange = layout.yearRange;
        const PADDING = 50;

        const xStart = xScale(yearRange.min) - PADDING;
        const xEnd = xScale(yearRange.max) + PADDING;

        const miniMinY = d3.min(nodes, n => n.y) || 50;
        const miniMaxY = d3.max(nodes, n => n.y + (n.height || 0)) || 50;
        const paddedMinY = miniMinY - PADDING;
        const paddedMaxY = miniMaxY + PADDING;

        const layoutWidth = xEnd - xStart;
        const layoutHeight = paddedMaxY - paddedMinY;

        if (layoutWidth <= 0 || layoutHeight <= 0) return;

        const scaleX = width / layoutWidth;
        const scaleY = height / layoutHeight;

        // Store scales in refs for drag handler
        scaleXRef.current = scaleX;
        scaleYRef.current = scaleY;

        const svg = d3.select(svgRef.current);
        svg.attr('width', width).attr('height', height);

        svg.selectAll('.minimap-node')
            .data(nodes, d => d.id)
            .join(
                enter => enter.append('rect')
                    .attr('class', 'minimap-node')
                    .attr('height', 0.5)
                    .attr('fill', '#888'),
                update => update,
                exit => exit.remove()
            )
            .attr('x', d => (d.x - xStart) * scaleX)
            .attr('y', d => (d.y - paddedMinY) * scaleY)
            .attr('width', d => d.width * scaleX);

        // Calculate Main Layout Bounds
        let mainBounds = null;
        if (mainLayout && mainLayout.nodes && mainLayout.nodes.length > 0) {
            mainBounds = {
                minY: d3.min(mainLayout.nodes, n => n.y) || 50,
                maxY: d3.max(mainLayout.nodes, n => n.y + (n.height || 0)) || 50
            };
        }

        // Store layout data for drag handler
        layoutDataRef.current = {
            yearRange,
            xScale,
            miniMinY,
            miniMaxY,
            mainBounds,
            xStart,
            paddedMinY
        };

        // Current view in Main World coordinates
        const currentTransform = transformRef.current;
        const visibleWorldX = -currentTransform.x / currentTransform.k;
        const visibleWorldY = -currentTransform.y / currentTransform.k;
        const visibleWorldW = containerDimensions.width / currentTransform.k;
        const visibleWorldH = containerDimensions.height / currentTransform.k;

        let minimapWorldX1, minimapWorldX2, minimapWorldY1, minimapWorldY2;

        if (mainLayout && mainBounds) {
            // X: Convert main world X to years, then years to minimap world X
            const mainMinYear = mainLayout.yearRange.min;
            const mainMaxYear = mainLayout.yearRange.max;
            const mainXStart = mainLayout.xScale(mainMinYear);
            const mainXEnd = mainLayout.xScale(mainMaxYear);
            const mainPixelsPerYear = (mainXEnd - mainXStart) / ((mainMaxYear - mainMinYear) || 1);

            const startYear = mainMinYear + (visibleWorldX - mainXStart) / mainPixelsPerYear;
            const endYear = mainMinYear + ((visibleWorldX + visibleWorldW) - mainXStart) / mainPixelsPerYear;

            minimapWorldX1 = xScale(startYear);
            minimapWorldX2 = xScale(endYear);

            // Y: Map via ratio
            const mainContentHeight = mainBounds.maxY - mainBounds.minY;
            const miniContentHeight = miniMaxY - miniMinY;

            if (mainContentHeight > 0 && miniContentHeight > 0) {
                const yRatioStart = (visibleWorldY - mainBounds.minY) / mainContentHeight;
                const yRatioEnd = (visibleWorldY + visibleWorldH - mainBounds.minY) / mainContentHeight;
                minimapWorldY1 = miniMinY + yRatioStart * miniContentHeight;
                minimapWorldY2 = miniMinY + yRatioEnd * miniContentHeight;
            } else {
                minimapWorldY1 = miniMinY;
                minimapWorldY2 = miniMinY + 100;
            }
        } else {
            minimapWorldX1 = xScale(yearRange.min);
            minimapWorldX2 = xScale(yearRange.max);
            minimapWorldY1 = 50;
            minimapWorldY2 = 150;
        }

        const rectX = (minimapWorldX1 - xStart) * scaleX;
        const rectY = (minimapWorldY1 - paddedMinY) * scaleY;
        const rectW = (minimapWorldX2 - minimapWorldX1) * scaleX;
        const rectH = (minimapWorldY2 - minimapWorldY1) * scaleY;

        const viewport = d3.select(viewportRef.current);
        viewport
            .attr('x', rectX)
            .attr('y', rectY)
            .attr('width', rectW)
            .attr('height', rectH);

    }, [layout, mainLayout, containerDimensions, dimensions, transform]);

    return (
        <div className="minimap-container" ref={containerRef} data-testid="minimap-container" style={{ width: '100%', height: '100%' }}>
            <svg ref={svgRef} data-testid="minimap-svg">
                <rect ref={viewportRef} className="minimap-viewport" data-testid="minimap-viewport-rect" />
            </svg>
        </div>
    );
}
