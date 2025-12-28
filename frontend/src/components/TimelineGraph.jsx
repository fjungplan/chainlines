import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';
import { LayoutCalculator } from '../utils/layoutCalculator';
import { validateGraphData } from '../utils/graphUtils';
import { VISUALIZATION } from '../constants/visualization';
import './TimelineGraph.css';
import { JerseyRenderer } from '../utils/jerseyRenderer';
import { ZoomLevelManager, ZOOM_THRESHOLDS } from '../utils/zoomLevelManager';
import { DetailRenderer } from '../utils/detailRenderer';
import ControlPanel from './ControlPanel';
import Tooltip from './Tooltip';
import { TooltipBuilder } from '../utils/tooltipBuilder';
import { GraphNavigation } from '../utils/graphNavigation';
import { ViewportManager } from '../utils/virtualization';
import { PerformanceMonitor } from '../utils/performanceMonitor';
import { OptimizedRenderer } from '../utils/optimizedRenderer';


import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

export default function TimelineGraph({
  data,
  onYearRangeChange,
  onTierFilterChange,
  initialStartYear = 2020,
  initialEndYear = new Date().getFullYear(),
  initialTiers = [1, 2, 3],
  onEditSuccess,
  currentStartYear,
  currentEndYear,
  filtersVersion = 0
}) {
  // DEBUG_TOGGLE: Set to false to hide viscous connector outlines + debug points
  const SHOW_VISCOSITY_DEBUG = false;
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const rulerTopRef = useRef(null);
  const rulerBottomRef = useRef(null);
  const zoomManager = useRef(null);
  const zoomBehavior = useRef(null);
  const currentLayout = useRef(null);
  const navigationRef = useRef(null);
  const viewportManager = useRef(null);
  const performanceMonitor = useRef(new PerformanceMonitor());
  const optimizedRenderer = useRef(null);
  const currentTransform = useRef(d3.zoomIdentity);
  const graphDataRef = useRef(null);
  const virtualizationTimeout = useRef(null);

  const [zoomLevel, setZoomLevel] = useState('OVERVIEW');
  const [tooltip, setTooltip] = useState({ visible: false, content: null, position: null });



  const [toast, setToast] = useState({ visible: false, message: '', type: 'success' });
  const [currentFilters, setCurrentFilters] = useState({
    startYear: currentStartYear || initialStartYear,
    endYear: currentEndYear || initialEndYear,
    isSidebarCollapsed: true
  });

  const VERTICAL_PADDING = VISUALIZATION.NODE_HEIGHT + 20;

  const { user, canEdit } = useAuth();
  const navigate = useNavigate();

  // Note: props-change effect moved below zoomToYearRange definition to avoid TDZ

  useEffect(() => {
    // Initialize zoom manager
    zoomManager.current = new ZoomLevelManager((level, scale) => {
      setZoomLevel(level);
    });

    // Initialize navigation manager
    if (svgRef.current && containerRef.current) {
      navigationRef.current = new GraphNavigation(
        svgRef.current,
        containerRef.current.clientWidth,
        containerRef.current.clientHeight
      );
    }

    // Initialize viewport and optimized renderer
    if (containerRef.current && svgRef.current) {
      viewportManager.current = new ViewportManager(
        containerRef.current.clientWidth,
        containerRef.current.clientHeight
      );
      optimizedRenderer.current = new OptimizedRenderer(
        svgRef.current,
        performanceMonitor.current
      );
    }
  }, []);

  // Helper to compute responsive minimum zoom
  // This is the "fit everything" scale - can't zoom out further than this
  const computeMinScale = useCallback((layout) => {
    const containerWidth = containerRef.current?.clientWidth || 1;
    const containerHeight = containerRef.current?.clientHeight || 1;

    const spanX = layout?.xScale
      ? layout.xScale(layout.yearRange.max) - layout.xScale(layout.yearRange.min)
      : 0;
    const nodes = layout?.nodes || [];
    const maxNodeBottom = nodes.length
      ? Math.max(...nodes.map(n => (n.y || 0) + (n.height || 0)))
      : 0;
    const minNodeTop = nodes.length ? Math.min(...nodes.map(n => n.y || 0)) : 0;
    const paddedMinY = minNodeTop - VERTICAL_PADDING;
    const paddedMaxY = maxNodeBottom + VERTICAL_PADDING;
    const spanY = Math.max(1, paddedMaxY - paddedMinY);

    if (!spanX || spanX <= 0) return VISUALIZATION.ZOOM_MIN;

    // Minimum scale is the one that fits BOTH dimensions
    // (the smaller of the two - more zoomed out)
    const scaleX = containerWidth / spanX;
    const scaleY = containerHeight / spanY;

    // Add safety floor of 0.01 to prevent invalid transforms
    return Math.max(0.01, Math.min(scaleX, scaleY));
  }, []);

  // Log performance metrics in development
  useEffect(() => {
    if (typeof process !== 'undefined' && process.env && process.env.NODE_ENV === 'development') {
      const interval = setInterval(() => {
        performanceMonitor.current.logMetrics();
      }, 10000);
      return () => clearInterval(interval);
    }
  }, []);

  useEffect(() => {
    if (!data || !data.nodes || !data.links) return;

    // Log raw API data to check for duplicates at source
    const nodeIds = data.nodes.map(n => n.id);
    const uniqueNodeIds = new Set(nodeIds);
    console.log('API Response - Total nodes:', nodeIds.length, 'Unique IDs:', uniqueNodeIds.size);
    if (nodeIds.length !== uniqueNodeIds.size) {
      const duplicates = nodeIds.filter((id, idx) => nodeIds.indexOf(id) !== idx);
      console.error('DUPLICATES IN API RESPONSE:', [...new Set(duplicates)]);
    }

    try {
      validateGraphData(data);
      renderGraph(data);
    } catch (error) {
      console.error('Graph render error:', error);
    }
  }, [data]);

  // Recalculate layout/zoom bounds on resize so minimum zoom remains responsive
  useEffect(() => {
    const handleResize = () => {
      if (currentLayout.current) {
        // Re-render with current layout when viewport changes
        if (viewportManager.current && svgRef.current && containerRef.current) {
          const container = containerRef.current;
          const width = container.clientWidth;
          const height = container.clientHeight;

          const layout = currentLayout.current;
          const minScale = computeMinScale(layout);
          zoomBehavior.current?.scaleExtent([minScale, VISUALIZATION.ZOOM_MAX]);

          // Trigger full re-render
          renderGraph(graphDataRef.current);
        }
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [computeMinScale]);

  // Prevent browser zoom on SVG container
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const preventBrowserZoom = (e) => {
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault();
      }
    };

    container.addEventListener('wheel', preventBrowserZoom, { passive: false });
    return () => container.removeEventListener('wheel', preventBrowserZoom);
  }, []);



  const handleZoom = useCallback((event) => {
    const { transform } = event;
    const g = d3.select(svgRef.current).select('g');
    g.attr('transform', transform);
    if (zoomManager.current) {
      zoomManager.current.updateScale(transform.k);
    }
  }, []);

  const handleZoomReset = useCallback(() => {
    zoomToYearRange(currentFilters.startYear, currentFilters.endYear);
  }, [currentFilters]);

  const zoomToYearRange = useCallback((startYear, endYear) => {
    if (!currentLayout.current || !svgRef.current || !containerRef.current || !zoomBehavior.current) return;

    const layout = currentLayout.current;
    const containerWidth = containerRef.current.clientWidth;

    const x1 = layout.xScale(startYear);
    const x2 = layout.xScale(endYear);
    const yearRangeWidth = Math.max(1, x2 - x1);

    const padding = 80;
    const rawScale = (containerWidth - 2 * padding) / yearRangeWidth;
    const minScale = computeMinScale(layout);
    const targetScale = Math.min(VISUALIZATION.ZOOM_MAX, Math.max(minScale, rawScale));

    const centerX = (x1 + x2) / 2;
    const targetX = containerWidth / 2 - centerX * targetScale;
    const targetY = 0;

    const svg = d3.select(svgRef.current);
    const transform = d3.zoomIdentity
      .translate(targetX, targetY)
      .scale(targetScale);

    svg.transition()
      .duration(750)
      .call(zoomBehavior.current.transform, transform);
  }, [computeMinScale]);

  // Update filters when props change and trigger zoom (defined after zoomToYearRange to avoid TDZ)
  useEffect(() => {
    if (currentStartYear !== undefined && currentEndYear !== undefined) {
      setCurrentFilters(prev => ({ ...prev, startYear: currentStartYear, endYear: currentEndYear }));
      if (currentLayout.current) {
        setTimeout(() => {
          zoomToYearRange(currentStartYear, currentEndYear);
        }, 50);
      }
    }
  }, [currentStartYear, currentEndYear, filtersVersion, zoomToYearRange]);

  const getGridInterval = (scale) => {
    // Only years or decades based on zoom level (grid switches earlier)
    return scale >= ZOOM_THRESHOLDS.HIGH_DETAIL ? 1 : 10;
  };

  const getLabelInterval = (scale) => {
    // Labels switch later to avoid overlap; stay on decades until more zoomed in
    return scale >= ZOOM_THRESHOLDS.RULER_DETAIL ? 1 : 10;
  };

  // --- Viscous connector fill styling (opaque + node-color gradient) ---
  const DEFAULT_NODE_COLOR = '#5a5a5a';
  const sanitizeSvgId = (s) => String(s).replace(/[^a-zA-Z0-9_-]/g, '_');

  const getNodePrimaryColor = (node) => {
    if (!node?.eras?.length) return DEFAULT_NODE_COLOR;

    // Aggregate prominence scores for all sponsors across all eras
    const sponsorScores = new Map(); // brandId -> { score, color }

    node.eras.forEach(era => {
      if (!era.sponsors) return;

      era.sponsors.forEach(sponsor => {
        // Use brand_id, brand name, or name as key
        // Logs showed 'brand' property holds the name
        const key = sponsor.id || sponsor.brand || sponsor.name;
        if (!key) return;

        const current = sponsorScores.get(key) || { score: 0, color: sponsor.color };

        // Add prominence to score (default to 0 if missing)
        current.score += Number(sponsor.prominence || 0);

        // Update color just in case (though it should be constant for the brand)
        if (sponsor.color) current.color = sponsor.color;

        sponsorScores.set(key, current);
      });
    });

    if (sponsorScores.size === 0) return DEFAULT_NODE_COLOR;

    // Find the sponsor with the highest total score
    let bestSponsor = null;
    let maxScore = -1;

    for (const [key, data] of sponsorScores) {
      if (data.score > maxScore) {
        maxScore = data.score;
        bestSponsor = data;
      }
    }

    return bestSponsor?.color || DEFAULT_NODE_COLOR;
  };

  const ensureLinkGradient = (defs, linkDatum, startColor, endColor) => {
    const id = sanitizeSvgId(`link-gradient-${linkDatum.source}-${linkDatum.target}-${linkDatum.year ?? 'na'}-${linkDatum.type ?? 'na'}`);

    let grad = defs.select(`#${id}`);
    if (grad.empty()) {
      grad = defs.append('linearGradient')
        .attr('id', id)
        .attr('x1', '0%')
        .attr('y1', '0%')
        .attr('x2', '0%')
        .attr('y2', '100%');
    }

    // Determine middle color based on link type
    // SPIRITUAL_SUCCESSION: source → white → target
    // Others (including LEGAL_TRANSFER): source → black → target
    const middleColor = linkDatum.type === 'SPIRITUAL_SUCCESSION' ? '#ffffff' : '#000000';
    const bandWidth = 2; // percentage width for the center band (very narrow highlight)
    const halfBand = bandWidth / 2;
    const midStart = Math.max(0, 50 - halfBand);
    const midEnd = Math.min(100, 50 + halfBand);
    const fadeWidth = 9; // how far the middle color fades into source/target colors
    const fadeBefore = Math.max(0, midStart - fadeWidth);
    const fadeAfter = Math.min(100, midEnd + fadeWidth);

    const stops = [
      { offset: '0%', color: startColor },
      { offset: `${fadeBefore}%`, color: startColor },
      { offset: `${midStart}%`, color: middleColor },
      { offset: `${midEnd}%`, color: middleColor },
      { offset: `${fadeAfter}%`, color: endColor },
      { offset: '100%', color: endColor }
    ];

    grad.selectAll('stop')
      .data(stops, (d) => d.offset)
      .join(
        (enter) => enter.append('stop'),
        (update) => update,
        (exit) => exit.remove()
      )
      .attr('offset', (d) => d.offset)
      .attr('stop-color', (d) => d.color);

    return id;
  };

  const renderBackgroundGrid = (g, layout, scale = 1) => {
    let gridGroup = g.select('.grid');
    if (gridGroup.empty()) {
      gridGroup = g.append('g')
        .attr('class', 'grid')
        .style('pointer-events', 'none');
    } else {
      gridGroup.selectAll('*').remove();
    }

    // Use actual year bounds and the same scale as layout
    const yearRange = layout?.yearRange ?? { min: 0, max: 1 };
    const xScale = layout?.xScale ?? ((year) => year);

    // Dynamic spacing by zoom level for grid only
    const interval = getGridInterval(scale);
    const gridSpacingYears = interval;

    // Draw vertical grid lines - extend to actual node bounds, not just viewport
    const start = Math.floor(yearRange.min / gridSpacingYears) * gridSpacingYears;
    const end = Math.ceil(yearRange.max / gridSpacingYears) * gridSpacingYears;
    const nodes = layout?.nodes || [];
    const maxNodeBottom = nodes.length
      ? Math.max(...nodes.map(n => (n.y || 0) + (n.height || 0)))
      : (containerRef.current?.clientHeight || 1000);
    const minNodeTop = nodes.length ? Math.min(...nodes.map(n => n.y || 0)) : -100;
    const paddedMinY = minNodeTop - VERTICAL_PADDING;
    const paddedMaxY = maxNodeBottom + VERTICAL_PADDING;

    for (let year = start; year <= end; year += gridSpacingYears) {
      const x = xScale(year);
      const isDecade = Math.abs(year % 10) < 0.1; // Float safety
      const isHighDetail = scale >= ZOOM_THRESHOLDS.HIGH_DETAIL;
      const highlightDecade = isDecade && isHighDetail;

      gridGroup.append('line')
        .attr('x1', x)
        .attr('y1', paddedMinY - 100)
        .attr('x2', x)
        .attr('y2', paddedMaxY + 100)
        .attr('stroke', highlightDecade ? '#777' : '#444')
        .attr('stroke-width', highlightDecade ? Math.max(1.2, 1.2 / scale) : Math.max(0.7, 0.7 / scale))
        .attr('stroke-dasharray', scale >= ZOOM_THRESHOLDS.GRID_DENSITY ? '1,3' : '3,3');
    }
  };


  const renderGraph = (graphData) => {
    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Deduplicate nodes by ID
    const deduplicatedNodes = [];
    const seenIds = new Set();
    const duplicateMap = {};

    for (const node of graphData.nodes) {
      if (!seenIds.has(node.id)) {
        deduplicatedNodes.push(node);
        seenIds.add(node.id);
      } else {
        duplicateMap[node.id] = (duplicateMap[node.id] || 1) + 1;
      }
    }

    if (deduplicatedNodes.length < graphData.nodes.length) {
      const removedCount = graphData.nodes.length - deduplicatedNodes.length;
      console.warn('Found duplicate nodes:', removedCount, duplicateMap);
      console.log('Original nodes:', graphData.nodes.map(n => ({ id: n.id, name: n.eras?.[0]?.name })));
      console.log('Deduplicated nodes:', deduplicatedNodes.map(n => ({ id: n.id, name: n.eras?.[0]?.name })));
    }

    console.log('Rendering with nodes:', deduplicatedNodes.map(n => ({
      id: n.id,
      name: n.eras?.[0]?.name,
      founding: n.founding_year,
      dissolution: n.dissolution_year,
      eras: n.eras?.length
    })));

    const dedupedData = {
      ...graphData,
      nodes: deduplicatedNodes
    };

    const layoutStart = performanceMonitor.current.startTiming('layout');
    // Extend the filter range by 1 year to show full span of the end year
    const filterYearRange = { min: currentFilters.startYear, max: currentFilters.endYear + 1 };
    let calculator = new LayoutCalculator(dedupedData, width, height, filterYearRange);
    let layout = calculator.calculateLayout();

    // If the container is wider relative to content height, stretch the x-axis to eliminate horizontal gutters
    const spanX = layout.xScale(layout.yearRange.max) - layout.xScale(layout.yearRange.min);
    const nodesForSpan = layout.nodes || [];
    const maxNodeBottom = nodesForSpan.length
      ? Math.max(...nodesForSpan.map(n => (n.y || 0) + (n.height || 0)))
      : height;
    const minNodeTop = nodesForSpan.length ? Math.min(...nodesForSpan.map(n => n.y || 0)) : 0;
    const paddedMinY = minNodeTop - VERTICAL_PADDING;
    const paddedMaxY = maxNodeBottom + VERTICAL_PADDING;
    const spanY = Math.max(1, paddedMaxY - paddedMinY);
    const scaleX = width / spanX;
    const scaleY = height / spanY;

    if (scaleX > scaleY * 1.001) {
      const stretchFactor = scaleX / scaleY;
      console.log('Applying x-axis stretch for aspect fit', { scaleX, scaleY, stretchFactor, spanX, spanY });
      calculator = new LayoutCalculator(dedupedData, width, height, filterYearRange, stretchFactor);
      layout = calculator.calculateLayout();
    }
    performanceMonitor.current.endTiming('layout', layoutStart);
    performanceMonitor.current.metrics.nodeCount = layout.nodes.length;
    performanceMonitor.current.metrics.linkCount = layout.links.length;
    currentLayout.current = layout;
    graphDataRef.current = graphData;

    // Perform actual rendering (will be called after all render functions are defined)
    renderGraphVirtualized(layout);
  };

  // This will be defined later after helper functions, but called from renderGraph
  const renderGraphVirtualized = (layout) => {
    if (!viewportManager.current || !layout) return;
    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Update zoom min scale when layout recalculates
    const minScale = computeMinScale(layout);
    zoomBehavior.current?.scaleExtent([minScale, VISUALIZATION.ZOOM_MAX]);

    // Calculate initial transform if this is first render (identity transform)
    if (currentTransform.current.k === 1 && currentTransform.current.x === 0 && currentTransform.current.y === 0) {
      const nodes = layout.nodes || [];

      if (nodes.length === 0) {
        console.error('No nodes to display!');
        return;
      }

      const maxNodeBottom = Math.max(...nodes.map(n => (n.y || 0) + (n.height || 0)));
      const minNodeTop = Math.min(...nodes.map(n => n.y || 0));
      const paddedMinY = minNodeTop - VERTICAL_PADDING;
      const paddedMaxY = maxNodeBottom + VERTICAL_PADDING;

      const spanX = layout.xScale(layout.yearRange.max) - layout.xScale(layout.yearRange.min);
      const spanY = Math.max(1, paddedMaxY - paddedMinY);

      // Initial scale: fit ALL content (both width and height)
      const scaleX = width / spanX;
      const scaleY = height / spanY;
      const targetScale = Math.max(0.01, Math.min(scaleX, scaleY));

      // Center the content in the viewport using padded bounds so labels don't overlap
      const centerX = (layout.xScale(layout.yearRange.min) + layout.xScale(layout.yearRange.max)) / 2;
      const centerY = (paddedMinY + paddedMaxY) / 2;
      const targetX = width / 2 - centerX * targetScale;
      const targetY = height / 2 - centerY * targetScale;

      console.log('🎯 INITIAL TRANSFORM CALC:', {
        nodeCount: nodes.length,
        yearRange: [layout.yearRange.min, layout.yearRange.max],
        spanX,
        spanY,
        containerWidth: width,
        containerHeight: height,
        scaleX,
        scaleY,
        targetScale,
        minScale,
        centerX,
        centerY,
        targetX,
        targetY,
        minNodeTop,
        maxNodeBottom,
        paddedMinY,
        paddedMaxY
      }); currentTransform.current = d3.zoomIdentity.translate(targetX, targetY).scale(targetScale);
    }

    // Use current transform
    const transform = currentTransform.current;

    const visibleNodes = viewportManager.current.getVisibleNodes(layout.nodes, transform);
    const visibleNodeIds = new Set(visibleNodes.map((n) => n.id));
    const visibleLinks = viewportManager.current.getVisibleLinks(layout.links, visibleNodeIds);

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();
    svg.attr('width', width).attr('height', height);

    // Add gradient definitions for different link styles
    const defs = svg.append('defs');

    // Gradient for MERGE connections (multiple sources converging)
    const mergeGradient = defs.append('linearGradient')
      .attr('id', 'mergeGradient')
      .attr('x1', '0%')
      .attr('y1', '0%')
      .attr('x2', '100%')
      .attr('y2', '0%');

    mergeGradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', VISUALIZATION.LINK_COLOR_LEGAL)
      .attr('stop-opacity', 0.6);

    mergeGradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', VISUALIZATION.LINK_COLOR_LEGAL)
      .attr('stop-opacity', 1);

    const g = svg.append('g');
    // Apply current transform immediately to avoid initial flash before zoom attaches
    g.attr('transform', currentTransform.current);

    // Add background grid
    renderBackgroundGrid(g, layout);
    JerseyRenderer.createShadowFilter(svg);

    // Layer order depends on debug toggle
    renderNodeShadows(g, visibleNodes);
    const currentScale = currentTransform.current.k;

    if (SHOW_VISCOSITY_DEBUG) {
      renderNodes(g, visibleNodes, svg, currentScale);
      renderLinks(g, visibleLinks);
    } else {
      renderLinks(g, visibleLinks);
      renderNodes(g, visibleNodes, svg, currentScale);
    }

    // Render transition markers
    renderTransitionMarkers(g, visibleLinks);

    arrangeLinkLayer(g);

    renderRulers(layout, transform);

    setupZoomWithVirtualization(svg, g, layout);
  };

  const renderNodeShadows = (g, nodes) => {
    let shadowLayer = g.select('.node-shadows');
    if (shadowLayer.empty()) {
      // Ensure shadows are behind links/nodes. Try to insert before links if they exist,
      // otherwise append (will settle correct order in initial render)
      const linkLayer = g.select('.links');
      if (!linkLayer.empty()) {
        shadowLayer = g.insert('g', '.links').attr('class', 'node-shadows');
      } else {
        shadowLayer = g.append('g').attr('class', 'node-shadows');
      }
    }
    shadowLayer
      .selectAll('.node-shadow')
      .data(nodes, (d) => d.id)
      .join('rect')
      .attr('class', 'node-shadow')
      .attr('x', (d) => d.x)
      .attr('y', (d) => d.y)
      .attr('width', (d) => d.width)
      .attr('height', (d) => d.height)
      .attr('rx', 0.5)
      .attr('ry', 0.5)
      .attr('filter', 'url(#drop-shadow)')
      .attr('fill', '#000')
      .attr('fill-opacity', 1)
      .style('pointer-events', 'none');
  };

  const arrangeLinkLayer = (g) => {
    const linksLayer = g.select('.links');
    const nodesLayer = g.select('.nodes');
    if (linksLayer.empty() || nodesLayer.empty()) return;
    const linksNode = linksLayer.node();
    const nodesNode = nodesLayer.node();
    const parent = linksNode?.parentNode;
    if (!parent || !nodesNode) return;

    if (SHOW_VISCOSITY_DEBUG) {
      parent.appendChild(linksNode);
    } else {
      parent.insertBefore(linksNode, nodesNode);
    }
  };

  const setupZoomWithVirtualization = (svg, g, layout) => {
    const containerWidth = containerRef.current?.clientWidth || 1;
    const containerHeight = containerRef.current?.clientHeight || 1;
    const minScale = computeMinScale(layout);

    // Constrain panning: calculate extent that prevents panning outside year bounds
    // translateExtent is in world coords, so we need to account for scale and pan
    const span = layout.xScale(layout.yearRange.max) - layout.xScale(layout.yearRange.min);
    const yearMin = layout.xScale(layout.yearRange.min);
    const yearMax = layout.xScale(layout.yearRange.max);

    const nodes = layout.nodes || [];
    const maxNodeBottom = nodes.length
      ? Math.max(...nodes.map(n => (n.y || 0) + (n.height || 0)))
      : containerHeight;
    const minNodeTop = nodes.length ? Math.min(...nodes.map(n => n.y || 0)) : 0;
    const paddedMinY = minNodeTop - VERTICAL_PADDING;
    const paddedMaxY = maxNodeBottom + VERTICAL_PADDING;

    // translateExtent defines the area that can be panned to
    // [[x0, y0], [x1, y1]] means: top-left corner can pan from x0,y0 to x1,y1
    // We want the viewport to never see empty space; keep extent tight to content + padding
    const extent = [
      [yearMin, paddedMinY],
      [yearMax, paddedMaxY]
    ];

    console.log('🔧 ZOOM SETUP:', {
      minScale,
      maxScale: VISUALIZATION.ZOOM_MAX,
      extent,
      currentTransform: { k: currentTransform.current.k, x: currentTransform.current.x, y: currentTransform.current.y },
      containerWidth,
      containerHeight,
      span,
      yearMin,
      yearMax
    });

    const zoom = d3
      .zoom()
      .scaleExtent([minScale, VISUALIZATION.ZOOM_MAX])
      .translateExtent(extent)
      .filter((event) => {
        // Allow mouse wheel, touch gestures, but block right-click drag
        if (event.type === 'wheel') return !event.ctrlKey;
        if (event.type === 'mousedown') return !event.button;
        return true; // Allow touch events
      })
      .on('zoom', (event) => {
        console.log('🎯 ZOOM EVENT:', { k: event.transform.k, x: event.transform.x, y: event.transform.y });
        currentTransform.current = event.transform;
        g.attr('transform', event.transform);

        // Zoom level manager and LOD updates
        if (zoomManager.current) {
          zoomManager.current.updateScale(event.transform.k);
        }
        if (optimizedRenderer.current) {
          optimizedRenderer.current.renderWithLOD(
            currentLayout.current?.nodes || [],
            currentLayout.current?.links || [],
            event.transform.k
          );
        }

        // Update grid density with zoom
        renderBackgroundGrid(g, layout, event.transform.k);
        renderRulers(layout, event.transform);

        // Debounce virtualization updates
        clearTimeout(virtualizationTimeout.current);
        virtualizationTimeout.current = setTimeout(() => {
          updateVirtualization(layout, event.transform);
        }, 100);
      });
    zoomBehavior.current = zoom;

    // Initialize zoom behavior and set the current transform
    svg.call(zoom);

    console.log('📍 BEFORE D3 TRANSFORM:', { k: currentTransform.current.k, x: currentTransform.current.x, y: currentTransform.current.y });

    // Always apply the current transform to D3's zoom state
    // This will trigger the zoom event handler which will set g.attr('transform')
    svg.call(zoom.transform, currentTransform.current);
    console.log('✅ APPLIED TRANSFORM TO D3');
  };

  const updateVirtualization = (layout, transform) => {
    if (!viewportManager.current) return;

    // Get visible data
    const visibleNodes = viewportManager.current.getVisibleNodes(layout.nodes, transform);
    const visibleNodeIds = new Set(visibleNodes.map((n) => n.id));
    const visibleLinks = viewportManager.current.getVisibleLinks(layout.links, visibleNodeIds);

    const g = d3.select(svgRef.current).select('g');
    const svg = d3.select(svgRef.current);
    const scale = transform.k;

    // Delegate to centralized render functions
    renderNodeShadows(g, visibleNodes);

    // Toggle debug view for links
    if (SHOW_VISCOSITY_DEBUG) {
      renderNodes(g, visibleNodes, svg, scale);
      renderLinks(g, visibleLinks);
    } else {
      renderLinks(g, visibleLinks);
      renderNodes(g, visibleNodes, svg, scale);
    }

    renderTransitionMarkers(g, visibleLinks);
    arrangeLinkLayer(g);
  };

  const renderRulers = useCallback((layout, transform = d3.zoomIdentity) => {
    if (!layout || !layout.xScale || !layout.yearRange) return;
    if (!rulerTopRef.current || !rulerBottomRef.current || !containerRef.current) return;

    const containerWidth = containerRef.current.clientWidth;
    const interval = getLabelInterval(transform.k || 1);
    const start = Math.floor(layout.yearRange.min / interval) * interval;
    const end = Math.ceil(layout.yearRange.max / interval) * interval;

    const positions = [];
    for (let year = start; year <= end; year += interval) {
      const midYear = year + interval / 2;
      const screenX = layout.xScale(midYear) * transform.k + transform.x;
      if (screenX < -100 || screenX > containerWidth + 100) continue;
      const label = interval >= 10 ? `${year}s` : `${year}`;
      positions.push({ x: screenX, label });
    }

    const renderInto = (ref) => {
      ref.innerHTML = '';
      positions.forEach(({ x, label }) => {
        const span = document.createElement('span');
        span.className = 'timeline-ruler-label';
        span.style.left = `${x}px`;
        span.textContent = label;
        ref.appendChild(span);
      });
    };

    renderInto(rulerTopRef.current);
    renderInto(rulerBottomRef.current);
  }, []);

  const renderLinks = (g, links) => {
    // Only render links with paths
    const linkData = links.filter(d => d.path !== null);

    let container = g.select('.links');
    if (container.empty()) {
      // Ensure links are behind nodes
      const nodeLayer = g.select('.nodes');
      if (!nodeLayer.empty()) {
        container = g.insert('g', '.nodes').attr('class', 'links');
      } else {
        container = g.append('g').attr('class', 'links');
      }
    }

    const svg = d3.select(svgRef.current);
    const defs = svg.select('defs').empty() ? svg.append('defs') : svg.select('defs');
    const nodesById = new Map((currentLayout.current?.nodes || []).map((n) => [n.id, n]));

    container
      .selectAll('g.link-container')
      .data(linkData, (d) => d.id || `${d.source}-${d.target}-${d.year || ''}-${d.type || ''}`)
      .join('g')
      .attr('class', 'link-container')
      .each(function (d) {
        const group = d3.select(this);

        // Fill
        const sourceNode = nodesById.get(d.source);
        const targetNode = nodesById.get(d.target);
        const sourceColor = getNodePrimaryColor(sourceNode);
        const targetColor = getNodePrimaryColor(targetNode);
        const sourceIsTop = (d.sourceY ?? 0) <= (d.targetY ?? 0);
        const startColor = sourceIsTop ? sourceColor : targetColor;
        const endColor = sourceIsTop ? targetColor : sourceColor;
        const gradId = ensureLinkGradient(defs, d, startColor, endColor);

        group.append('path')
          .attr('class', 'link-fill')
          .attr('d', d.path)
          .attr('fill', `url(#${gradId})`)
          .attr('fill-opacity', 1)
          .attr('stroke', 'none')
          .style('cursor', 'pointer')
          .on('mouseenter', (event) => {
            const content = TooltipBuilder.buildLinkTooltip(d, currentLayout.current?.nodes || []);
            if (content) {
              setTooltip({ visible: true, content, position: { x: event.pageX, y: event.pageY } });
            }
          })
          .on('mousemove', (event) => {
            if (tooltip.visible) {
              setTooltip(prev => ({ ...prev, position: { x: event.pageX, y: event.pageY } }));
            }
          })
          .on('mouseleave', (event) => {
            setTooltip({ visible: false, content: null, position: null });
          });

        // DEBUG outlines + points (toggle via SHOW_VISCOSITY_DEBUG)
        if (SHOW_VISCOSITY_DEBUG && d.topPathD) {
          group.append('path')
            .attr('class', 'link-outline-top')
            .attr('d', d.topPathD)
            .attr('fill', 'none')
            .attr('stroke', 'red')
            .attr('stroke-width', 1.5)
            .attr('stroke-dasharray', '3,2')
            .style('pointer-events', 'none');
        } else {
          group.append('path').attr('class', 'link-outline-top').style('display', 'none');
        }

        if (SHOW_VISCOSITY_DEBUG && d.bottomPathD) {
          group.append('path')
            .attr('class', 'link-outline-bottom')
            .attr('d', d.bottomPathD)
            .attr('fill', 'none')
            .attr('stroke', 'blue')
            .attr('stroke-width', 1.5)
            .attr('stroke-dasharray', '3,2')
            .style('pointer-events', 'none');
        } else {
          group.append('path').attr('class', 'link-outline-bottom').style('display', 'none');
        }

        if (SHOW_VISCOSITY_DEBUG && d.debugPoints) {
          const pointsGroup = group.append('g').attr('class', 'debug-points');
          Object.entries(d.debugPoints).forEach(([key, p]) => {
            const pg = pointsGroup.append('g').attr('transform', `translate(${p.x},${p.y})`);
            // Smaller and thinner debug visuals
            pg.append('line').attr('x1', -1.5).attr('y1', -1.5).attr('x2', 1.5).attr('y2', 1.5).attr('stroke', 'yellow').attr('stroke-width', 0.5);
            pg.append('line').attr('x1', -1.5).attr('y1', 1.5).attr('x2', 1.5).attr('y2', -1.5).attr('stroke', 'yellow').attr('stroke-width', 0.5);
            pg.append('text').attr('y', -2.5).attr('text-anchor', 'middle').attr('fill', 'yellow').attr('font-size', '5px').text(key);
          });
        } else {
          group.append('g').attr('class', 'debug-points').style('display', 'none');
        }

        if (SHOW_VISCOSITY_DEBUG && d.bezierDebugPoints?.length) {
          const bezierGroup = group.append('g').attr('class', 'bezier-debug-points');
          d.bezierDebugPoints.forEach((p) => {
            const gp = bezierGroup.append('g').attr('class', 'bezier-point')
              .attr('transform', `translate(${p.x},${p.y})`);
            gp.append('circle')
              .attr('r', 1)
              .attr('fill', 'yellow')
              .style('pointer-events', 'none');
            gp.append('text')
              .attr('text-anchor', 'middle')
              .attr('dominant-baseline', 'central')
              .attr('fill', '#000')
              .attr('font-size', '2.5px')
              .text(p.label ?? '');
          });
        } else {
          group.append('g').attr('class', 'bezier-debug-points').style('display', 'none');
        }
      });
  };

  const renderTransitionMarkers = (g, links) => {
    // Only render markers for same-swimlane transitions
    const markerData = links.filter(d => d.sameSwimlane && d.path === null);

    let markerGroup = g.select('.transition-markers');
    if (markerGroup.empty()) {
      markerGroup = g.append('g').attr('class', 'transition-markers');
    }

    const markers = markerGroup
      .selectAll('g.transition-marker')
      .data(markerData, (d) => `marker-${d.source}-${d.target}-${d.year || ''}`)
      .join('g')
      .attr('class', 'transition-marker')
      .style('cursor', 'pointer')
      .on('mouseenter', (event, d) => {
        d3.select(event.currentTarget).select('line').attr('stroke-width', 3);
        d3.select(event.currentTarget).select('circle').attr('r', 5);
        const content = TooltipBuilder.buildLinkTooltip(d, currentLayout.current?.nodes || []);
        if (content) {
          setTooltip({ visible: true, content, position: { x: event.pageX, y: event.pageY } });
        }
      })
      .on('mousemove', (event) => {
        if (tooltip.visible) {
          setTooltip(prev => ({ ...prev, position: { x: event.pageX, y: event.pageY } }));
        }
      })
      .on('mouseleave', (event) => {
        d3.select(event.currentTarget).select('line').attr('stroke-width', 2);
        d3.select(event.currentTarget).select('circle').attr('r', 3.5);
        setTooltip({ visible: false, content: null, position: null });
      });

    // Vertical line marker
    markers
      .append('line')
      .attr('x1', (d) => d.targetX)
      .attr('y1', (d) => d.targetY - 15)
      .attr('x2', (d) => d.targetX)
      .attr('y2', (d) => d.targetY + 15)
      .attr('stroke', (d) =>
        d.type === 'SPIRITUAL_SUCCESSION' ? VISUALIZATION.LINK_COLOR_SPIRITUAL : VISUALIZATION.LINK_COLOR_LEGAL
      )
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', (d) => (d.type === 'SPIRITUAL_SUCCESSION' ? '4,2' : '0'));

    // Circle at center
    markers
      .append('circle')
      .attr('cx', (d) => d.targetX)
      .attr('cy', (d) => d.targetY)
      .attr('r', 3.5)
      .attr('fill', (d) =>
        d.type === 'SPIRITUAL_SUCCESSION' ? VISUALIZATION.LINK_COLOR_SPIRITUAL : VISUALIZATION.LINK_COLOR_LEGAL
      )
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5);
  };


  const renderNodes = (g, nodes, svg, scale) => {
    const isHighDetail = scale >= ZOOM_THRESHOLDS.DETAIL_VISIBLE;

    // Ensure container exists
    const container = g.select('.nodes').empty() ? g.append('g').attr('class', 'nodes') : g.select('.nodes');

    container.selectAll('.node')
      .data(nodes, d => d.id)
      .join(
        enter => {
          const group = enter.append('g')
            .attr('class', 'node')
            .attr('data-id', d => d.id)
            .attr('transform', d => `translate(${d.x},${d.y})`)
            .style('cursor', 'pointer')
            .on('click', (event, d) => handleNodeClick(d))
            .on('mouseenter', (event, d) => {
              handleNodeHover(event, d);
            })
            .on('mousemove', (event) => {
              if (tooltip.visible) {
                setTooltip(prev => ({ ...prev, position: { x: event.pageX, y: event.pageY } }));
              }
            })
            .on('mouseleave', (event) => {
              handleNodeHoverEnd(event);
              setTooltip({ visible: false, content: null, position: null });
            });


          // Labels will be ensured in the merge .each() block
          return group;
        },
        update => update.attr('transform', d => `translate(${d.x},${d.y})`),
        exit => exit.remove()
      )
      .each(function (d) {
        const group = d3.select(this);

        // 0. Ensure Labels (if not present - e.g. virtualization edge cases, though join should handle)
        if (group.select('text').empty()) {
          JerseyRenderer.addNodeLabel(group, d);
        }

        // 1. Toggle Labels
        // Visible if scale < HIGH_DETAIL (1.2)
        const isLabelVisible = scale < ZOOM_THRESHOLDS.HIGH_DETAIL;
        group.selectAll('text').style('display', isLabelVisible ? null : 'none');

        // 2. Base Node Rect (Solid Color) - Nested Join
        // Visible only if NOT high detail
        const baseData = isHighDetail ? [] : [1];
        group.selectAll('.node-base')
          .data(baseData)
          .join(
            enter => enter.insert('rect', ':first-child') // Insert behind everything
              .attr('class', 'node-base')
              .attr('width', d.width)
              .attr('height', d.height)
              .attr('rx', 0.5)
              .attr('ry', 0.5)
              .attr('shape-rendering', 'crispEdges')
              .attr('fill', getNodePrimaryColor(d)),
            update => update
              .attr('width', d.width)
              .attr('height', d.height)
              .attr('fill', getNodePrimaryColor(d)),
            exit => exit.remove()
          );

        // 3. Eras (High Detail) - DetailRenderer handles internal 1.2 threshold for gradients
        if (isHighDetail) {
          DetailRenderer.renderEraTimeline(group, d, scale, svg, handleEraHover, handleEraHoverEnd);
        } else {
          group.selectAll('.era-segment').remove();
        }
      });
  };

  const handleTeamSelect = useCallback((node) => {
    if (navigationRef.current) {
      navigationRef.current.focusOnNode(node);
    }
  }, []);

  const handleNodeClick = (node) => {
    // Navigate to team detail page for all users (replacing old Edit wizard)
    navigate(`/team/${node.id}`);
  };

  const showToast = (message, type = 'success', duration = 3000) => {
    setToast({ visible: true, message, type });
    setTimeout(() => {
      setToast({ visible: false, message: '', type: 'success' });
    }, duration);
  };



  const handleNodeHover = (event, node) => {
    // Context-aware tooltip:
    // If scale < HIGH_DETAIL, show Node Summary.
    // If scale >= HIGH_DETAIL, eras handles interaction (or no tooltip if hovering gap).
    const currentScale = currentTransform.current ? currentTransform.current.k : 1;
    if (currentScale < ZOOM_THRESHOLDS.HIGH_DETAIL) {
      const content = TooltipBuilder.buildNodeTooltip(node);
      setTooltip({ visible: true, content, position: { x: event.pageX, y: event.pageY } });
    }
  };

  const handleNodeHoverEnd = (event) => {
    // Always clear tooltip on leave
    if (tooltip.visible) {
      setTooltip({ visible: false, content: null, position: null });
    }
  };

  const handleEraHover = (event, era, node) => {
    // Show Era Tooltip
    // Note: Event might need to be stopped from propagating if necessary, but SVG events are specific.
    event.stopPropagation();
    const content = TooltipBuilder.buildEraTooltip(era, node);
    setTooltip({ visible: true, content, position: { x: event.pageX, y: event.pageY } });
  };

  const handleEraHoverEnd = (event) => {
    event.stopPropagation();
    setTooltip({ visible: false, content: null, position: null });
  };

  return (
    <div className="timeline-layout">
      <div
        ref={containerRef}
        className="timeline-graph-container"
      >
        <div className="timeline-ruler top" ref={rulerTopRef} aria-hidden="true" />
        <div className="timeline-ruler bottom" ref={rulerBottomRef} aria-hidden="true" />
        <div className="timeline-copyright" aria-label="Copyright">
          © 2025 - {new Date().getFullYear()} ChainLines
        </div>
        <svg ref={svgRef}></svg>
      </div>
      <div className={`timeline-sidebar ${currentFilters.isSidebarCollapsed ? 'collapsed' : ''}`}>
        <button
          className="sidebar-toggle-btn"
          onClick={() => setCurrentFilters(prev => ({ ...prev, isSidebarCollapsed: !prev.isSidebarCollapsed }))}
          aria-label={currentFilters.isSidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          title={currentFilters.isSidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {currentFilters.isSidebarCollapsed ? (
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M15 18l-6-6 6-6" />
            </svg> // Left arrow (expand) - assumes sidebar on right
          ) : (
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 18l6-6-6-6" />
            </svg> // Right arrow (collapse) - assumes sidebar on right
          )}
        </button>

        <div className="sidebar-content">
          <ControlPanel
            onYearRangeChange={onYearRangeChange}
            onTierFilterChange={onTierFilterChange}
            onZoomReset={handleZoomReset}
            onTeamSelect={handleTeamSelect}
            searchNodes={data?.nodes || []}
            initialStartYear={initialStartYear}
            initialEndYear={initialEndYear}
            initialTiers={initialTiers}
          />


        </div>
      </div>

      <Tooltip
        content={tooltip.content}
        position={tooltip.position}
        visible={tooltip.visible}
      />





      {/* Toast Notification */}
      {toast.visible && (
        <div className={`toast toast-${toast.type}`}>
          <div className="toast-content">
            {toast.type === 'success' && <span className="toast-icon">✓</span>}
            {toast.type === 'info' && <span className="toast-icon">ℹ</span>}
            {toast.type === 'error' && <span className="toast-icon">✕</span>}
            <span className="toast-message">{toast.message}</span>
          </div>
        </div>
      )}
    </div>
  );
}
