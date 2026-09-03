// This module defines the minimum desktop readability baseline used by
// deterministic artifact checks. Broader browser evidence coverage lives in
// visual-check and is intentionally stricter than this baseline gate.
export const DESKTOP_READABILITY_BASELINE_VIEWPORT = Object.freeze({ width: 1440, height: 900 });
export const DESKTOP_READER_MIN_WIDTH = 960;
export const DESKTOP_READER_HORIZONTAL_CHROME = 30;
export const DESKTOP_READER_DIAGRAM_WIDTH = DESKTOP_READER_MIN_WIDTH - DESKTOP_READER_HORIZONTAL_CHROME;
export const MINIMUM_BASELINE_PROJECTED_NODE_TEXT_PX = 6;

// Backward-compatible aliases for existing imports.
export const DESKTOP_READABILITY_VIEWPORT = DESKTOP_READABILITY_BASELINE_VIEWPORT;
export const MIN_PROJECTED_NODE_TEXT_PX = MINIMUM_BASELINE_PROJECTED_NODE_TEXT_PX;

export function projectedNodeTextPx(sourceFontPx, viewBoxWidth, diagramWidth = DESKTOP_READER_DIAGRAM_WIDTH) {
  if (![sourceFontPx, viewBoxWidth, diagramWidth].every(Number.isFinite) || viewBoxWidth <= 0 || diagramWidth <= 0) {
    return Number.NaN;
  }
  return sourceFontPx * Math.min(1, diagramWidth / viewBoxWidth);
}

export function minimumReadableSourceTextPx(
  viewBoxWidth,
  diagramWidth = DESKTOP_READER_DIAGRAM_WIDTH,
  minimumProjectedPx = MIN_PROJECTED_NODE_TEXT_PX,
) {
  if (![viewBoxWidth, diagramWidth, minimumProjectedPx].every(Number.isFinite)
    || viewBoxWidth <= 0
    || diagramWidth <= 0
    || minimumProjectedPx <= 0) {
    return Number.NaN;
  }
  return minimumProjectedPx / Math.min(1, diagramWidth / viewBoxWidth);
}
