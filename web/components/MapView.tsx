"use client";
import { useEffect, useRef, useState } from "react";
import type { GeoJSONSource, Map as MlMap, MapMouseEvent } from "maplibre-gl";
import { DATA } from "@/lib/data";
import type { Bbox } from "@/lib/types";

interface Props {
  aoiShape: GeoJSON.Geometry | null;
  fitBbox: Bbox | null;
  coverage: Bbox;
  drawing: boolean;
  onBox: (b: Bbox) => void;
  onDistrict: (id: string) => void;
}

function cssVar(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || "#888";
}

/** Keyless map: a plain background plus district outlines from districts.geojson (no tiles, no API key). */
export function MapView({ aoiShape, fitBbox, coverage, drawing, onBox, onDistrict }: Props) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<MlMap | null>(null);
  const [ready, setReady] = useState(false);
  const drawingRef = useRef(drawing);
  const cb = useRef({ onBox, onDistrict });
  cb.current = { onBox, onDistrict };
  drawingRef.current = drawing;
  const shapeRef = useRef(aoiShape);
  shapeRef.current = aoiShape;
  const fitRef = useRef(fitBbox);
  fitRef.current = fitBbox;

  useEffect(() => {
    let cancelled = false;
    let cleanup: (() => void) | undefined;
    void import("maplibre-gl").then((ml) => {
      if (cancelled || !el.current) return;
      ml.setWorkerUrl(new URL("/maplibre/maplibre-gl-worker.mjs", window.location.href).href);
      const m = new ml.Map({
        container: el.current,
        style: {
          version: 8,
          sources: {
            districts: { type: "geojson", data: `${DATA}/districts.geojson`, attribution: "Boundaries: geoBoundaries (IND ADM2 ODbL 1.0)" },
            aoi: { type: "geojson", data: { type: "FeatureCollection", features: [] } },
          },
          layers: [
            { id: "bg", type: "background", paint: { "background-color": cssVar("--sheet") } },
            { id: "d-fill", type: "fill", source: "districts", paint: { "fill-color": cssVar("--paper"), "fill-opacity": 0.9 } },
            { id: "d-line", type: "line", source: "districts", paint: { "line-color": cssVar("--rule"), "line-width": 0.6 } },
            { id: "aoi-fill", type: "fill", source: "aoi", paint: { "fill-color": cssVar("--accent"), "fill-opacity": 0.18 } },
            { id: "aoi-line", type: "line", source: "aoi", paint: { "line-color": cssVar("--accent"), "line-width": 2 } },
          ],
        },
        bounds: [[coverage[0], coverage[1]], [coverage[2], coverage[3]]],
        attributionControl: { compact: true },
        // Coarse pointers (phones): one finger scrolls the page, two fingers move the map (MapLibre cooperative gestures). Drawing switches this off.
        cooperativeGestures: window.matchMedia("(pointer: coarse)").matches,
        dragRotate: false,
        pitchWithRotate: false,
      });
      m.touchZoomRotate.disableRotation();
      m.addControl(new ml.NavigationControl({ showCompass: false }), "top-right");
      map.current = m;
      // Named map region for screen readers (A11Y #9); the combobox is the keyboard path.
      m.getCanvas().setAttribute("aria-label", "Map of districts. Use the district search to select by keyboard.");

      // Drawing uses Pointer Events on the canvas (mouse, touch and pen share one path, D-046).
      // pointerdown captures the pointer; the first corner is the exact point under it and the
      // opposite corner follows it 1:1. A second pointer (pinch) cancels the draft; pointercancel
      // and lost capture discard it. Pan/zoom are disabled and touch-action is none only while
      // draw mode is on (see the drawing effect below).
      const canvas = m.getCanvas();
      let start: [number, number] | null = null;
      let pid: number | null = null;
      let justDrew = false; // the click that ends a drag must not also select a district
      const active = new Set<number>();
      const at = (e: PointerEvent): [number, number] => {
        const r = canvas.getBoundingClientRect();
        const ll = m.unproject([e.clientX - r.left, e.clientY - r.top]);
        return [ll.lng, ll.lat];
      };
      const setDraft = (a: [number, number], b: [number, number]) => {
        const src = m.getSource("aoi") as GeoJSONSource | undefined;
        src?.setData({ type: "Feature", properties: {}, geometry: { type: "Polygon", coordinates: [[[a[0], a[1]], [b[0], a[1]], [b[0], b[1]], [a[0], b[1]], [a[0], a[1]]]] } });
      };
      const restore = () => {
        const g = shapeRef.current;
        (m.getSource("aoi") as GeoJSONSource | undefined)?.setData(g ? { type: "Feature", properties: {}, geometry: g } : { type: "FeatureCollection", features: [] });
      };
      const abort = () => { if (start) { start = null; pid = null; restore(); } };
      const onDown = (e: PointerEvent) => {
        if (!drawingRef.current) return;
        active.add(e.pointerId);
        if (active.size > 1) { abort(); return; } // second finger: ignore the pinch
        if (e.pointerType === "mouse" && e.button !== 0) return;
        e.preventDefault();
        try { canvas.setPointerCapture(e.pointerId); } catch { /* pointer already gone */ }
        pid = e.pointerId;
        start = at(e);
        setDraft(start, start);
      };
      const onMove = (e: PointerEvent) => {
        if (!start || e.pointerId !== pid) return;
        setDraft(start, at(e));
      };
      const onUp = (e: PointerEvent) => {
        active.delete(e.pointerId);
        if (!start || e.pointerId !== pid) return;
        const a = start, end = at(e);
        start = null;
        pid = null;
        justDrew = true;
        setTimeout(() => { justDrew = false; }, 0);
        const b: Bbox = [Math.min(a[0], end[0]), Math.min(a[1], end[1]), Math.max(a[0], end[0]), Math.max(a[1], end[1])];
        if (b[2] - b[0] > 0.01 && b[3] - b[1] > 0.01) cb.current.onBox(b.map((v) => Math.round(v * 1000) / 1000) as Bbox);
        else restore();
      };
      const onCancel = (e: PointerEvent) => { active.delete(e.pointerId); if (e.pointerId === pid) abort(); };
      canvas.addEventListener("pointerdown", onDown);
      canvas.addEventListener("pointermove", onMove);
      canvas.addEventListener("pointerup", onUp);
      canvas.addEventListener("pointercancel", onCancel);
      canvas.addEventListener("lostpointercapture", onCancel);
      const click = (e: MapMouseEvent) => {
        if (drawingRef.current || justDrew) return;
        const f = m.queryRenderedFeatures(e.point, { layers: ["d-fill"] })[0];
        const id = f?.properties?.id;
        if (typeof id === "string") cb.current.onDistrict(id);
      };
      m.on("click", click);
      // Expose view state for tests (read-only attributes).
      const publish = () => {
        const c = m.getCenter();
        if (el.current) { el.current.dataset.lng = String(c.lng); el.current.dataset.lat = String(c.lat); el.current.dataset.zoom = String(m.getZoom()); }
      };
      m.on("moveend", publish);
      m.on("idle", publish);
      // The map may be created inside the collapsed phone panel (display: none, 0 size): resize and refit when it appears.
      const ro = new ResizeObserver(() => {
        if (!el.current || el.current.clientWidth === 0) return;
        m.resize();
        const f = fitRef.current;
        if (f) m.fitBounds([[f[0], f[1]], [f[2], f[3]]], { padding: 40, duration: 0, maxZoom: 8 });
        publish();
      });
      ro.observe(el.current);
      m.on("load", () => setReady(true));
      // Repaint with the theme tokens when the theme changes.
      const repaint = () => {
        m.setPaintProperty("bg", "background-color", cssVar("--sheet"));
        m.setPaintProperty("d-fill", "fill-color", cssVar("--paper"));
        m.setPaintProperty("d-line", "line-color", cssVar("--rule"));
        m.setPaintProperty("aoi-fill", "fill-color", cssVar("--accent"));
        m.setPaintProperty("aoi-line", "line-color", cssVar("--accent"));
      };
      const obs = new MutationObserver(() => { if (m.isStyleLoaded()) repaint(); });
      obs.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
      cleanup = () => { obs.disconnect(); ro.disconnect(); m.remove(); };
    });
    return () => {
      cancelled = true;
      cleanup?.();
      map.current = null;
    };
    // The map is created once; props are pushed in by the effects below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const m = map.current;
    if (!m || !ready) return;
    const apply = () => {
      const src = m.getSource("aoi") as GeoJSONSource | undefined;
      src?.setData(aoiShape ? { type: "Feature", properties: {}, geometry: aoiShape } : { type: "FeatureCollection", features: [] });
      if (fitBbox) m.fitBounds([[fitBbox[0], fitBbox[1]], [fitBbox[2], fitBbox[3]]], { padding: 40, duration: 0, maxZoom: 8 });
    };
    apply();
  }, [aoiShape, fitBbox, ready]);

  useEffect(() => {
    const m = map.current;
    if (!m) return;
    const canvas = m.getCanvas();
    canvas.style.cursor = drawing ? "crosshair" : "";
    // touch-action: none only while drawing, so panning and page scroll work the rest of the time.
    canvas.style.touchAction = drawing ? "none" : "";
    if (drawing) { m.cooperativeGestures.disable(); m.dragPan.disable(); m.touchZoomRotate.disable(); }
    else {
      m.dragPan.enable(); m.touchZoomRotate.enable(); m.touchZoomRotate.disableRotation();
      if (window.matchMedia("(pointer: coarse)").matches) m.cooperativeGestures.enable();
    }
  }, [drawing, ready]);

  return <div ref={el} className="map" role="region" aria-label="Map of districts. Click a district to select it, or use Draw box." data-testid="map" />;
}
