/**
 * MapLibre + Geoman + Alpine.js Integration
 * For use with Django projects
 */

function mapApp() {
  return {
    map: null,
    geoman: null,
    hoveredFeatureId: null,
    selectedFeatureIds: new Set(),
    selectedFeatures: [],
    hoveredFeature: null,
    gmEvents: [],
    expandedGeoJsonIndex: -1,
    isAnyGeomanModeActive: false,
    measurementPopup: null,
    isDrawingMode: false,
    currentDrawingCoordinates: [],
    drawingShape: null,

    /**
     * Initialize the map and all event listeners
     * Called by Alpine.js x-init directive
     */
    initMap() {
      // Initialize PMTiles protocol
      const protocol = new pmtiles.Protocol();
      maplibregl.addProtocol("pmtiles", protocol.tile);

      // Create map
      this.map = new maplibregl.Map({
        container: "map",
        style: this.getMapStyle(),
        center: [-93.05, 44.7],
        zoom: 10,
        fadeDuration: 50,
        minZoom: 0,
        maxZoom: 18,
      });

      // Initialize Geoman
      const gmOptions = {
        controls: {
          helper: {
            snapping: {
              uiEnabled: true,
              active: false,
            },
          },
        },
      };
      this.geoman = new Geoman(this.map, gmOptions);

      // Setup event listeners
      this.map.on("load", () => {
        this.setupMapListeners();
        this.setupGeomanListeners();
        this.checkPlatQueryParam();
      });

      this.map.on("error", (e) => {
        console.error("Map error:", e);
      });
    },

    /**
     * Define the MapLibre style specification
     * UPDATE: Change the PMTiles URL to point to your Django static/media files
     */
    getMapStyle() {
      return {
        version: 8,
        glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
        sources: {
          "osm-tiles": {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution: "© OpenStreetMap contributors",
          },
          protomaps: {
            type: "vector",
            url: "/parcel.pmtiles",
            promoteId: "TAXPIN",
          },
        },
        layers: [
          {
            id: "osm-tiles-layer",
            type: "raster",
            source: "osm-tiles",
            minzoom: 0,
            maxzoom: 19,
          },
          {
            id: "pmtiles-fill-default",
            source: "protomaps",
            "source-layer": "DAK_Parcel_Data_ENHANCED",
            type: "fill",
            paint: {
              "fill-color": [
                "case",
                ["boolean", ["feature-state", "selected"], false],
                "rgba(0, 100, 255, 0.7)",
                ["boolean", ["feature-state", "hover"], false],
                "rgba(255, 0, 0, 0.7)",
                "rgba(255, 0, 0, 0.3)",
              ],
              "fill-outline-color": [
                "case",
                ["boolean", ["feature-state", "selected"], false],
                "#0064ff",
                "#ff0000",
              ],
            },
            minzoom: 0,
            maxzoom: 18,
          },
        ],
      };
    },

    /**
     * Setup map event listeners for hover and click interactions
     */
    setupMapListeners() {
      // Mouse move handler
      this.map.on("mousemove", (e) => {
        // Handle live drawing measurements
        if (this.isDrawingMode) {
          this.showLiveDrawingMeasurement([e.lngLat.lng, e.lngLat.lat]);
        }

        // Skip feature hover when Geoman mode is active
        if (this.isAnyGeomanModeActive) {
          if (this.hoveredFeatureId !== null) {
            this.clearHover();
          }
          return;
        }

        const features = this.map.queryRenderedFeatures(e.point, {
          layers: ["pmtiles-fill-default"],
        });

        if (features.length > 0) {
          const feature = features[0];
          const featureId = feature.properties?.TAXPIN || feature.id;

          if (featureId !== this.hoveredFeatureId) {
            if (this.hoveredFeatureId !== null) {
              this.map.setFeatureState(
                {
                  source: "protomaps",
                  sourceLayer: "DAK_Parcel_Data_ENHANCED",
                  id: this.hoveredFeatureId,
                },
                { hover: false }
              );
            }

            this.map.setFeatureState(
              {
                source: "protomaps",
                sourceLayer: "DAK_Parcel_Data_ENHANCED",
                id: featureId,
              },
              { hover: true }
            );

            this.hoveredFeatureId = featureId;
            this.hoveredFeature = feature;
            this.map.getCanvas().style.cursor = "pointer";
          }
        } else {
          if (this.hoveredFeatureId !== null) {
            this.clearHover();
          }
        }
      });

      // Click handler for feature selection
      this.map.on("click", (e) => {
        // Track coordinates during drawing
        if (this.isDrawingMode) {
          this.currentDrawingCoordinates.push([e.lngLat.lng, e.lngLat.lat]);
          return;
        }

        // Skip selection when Geoman mode is active
        if (this.isAnyGeomanModeActive) {
          return;
        }

        const features = this.map.queryRenderedFeatures(e.point, {
          layers: ["pmtiles-fill-default"],
        });

        if (features.length > 0) {
          const feature = features[0];
          const featureId = feature.properties?.TAXPIN || feature.id;
          const isCtrlOrCmd =
            e.originalEvent.ctrlKey || e.originalEvent.metaKey;

          if (isCtrlOrCmd) {
            // Multi-select mode
            if (this.selectedFeatureIds.has(featureId)) {
              // Deselect
              this.selectedFeatureIds.delete(featureId);
              this.selectedFeatures = this.selectedFeatures.filter(
                (f) => (f.properties?.TAXPIN || f.id) !== featureId
              );
              this.map.setFeatureState(
                {
                  source: "protomaps",
                  sourceLayer: "DAK_Parcel_Data_ENHANCED",
                  id: featureId,
                },
                { selected: false }
              );
            } else {
              // Add to selection
              this.selectedFeatureIds.add(featureId);
              this.selectedFeatures.push(feature);
              this.map.setFeatureState(
                {
                  source: "protomaps",
                  sourceLayer: "DAK_Parcel_Data_ENHANCED",
                  id: featureId,
                },
                { selected: true }
              );
            }
          } else {
            // Single select mode
            this.clearAllSelections();
            this.selectedFeatureIds.add(featureId);
            this.selectedFeatures = [feature];
            this.map.setFeatureState(
              {
                source: "protomaps",
                sourceLayer: "DAK_Parcel_Data_ENHANCED",
                id: featureId,
              },
              { selected: true }
            );
          }
        } else {
          // Clear selection when clicking empty area
          if (!e.originalEvent.ctrlKey && !e.originalEvent.metaKey) {
            this.clearAllSelections();
          }
        }
      });
    },

    /**
     * Setup Geoman event listeners for drawing and editing
     */
    setupGeomanListeners() {
      this.map.on("gm:globaldrawmodetoggled", (e) => {
        this.isAnyGeomanModeActive = e.enabled;
        this.isDrawingMode = e.enabled;

        if (e.enabled) {
          this.currentDrawingCoordinates = [];
          this.drawingShape = e.shape || null;
        } else {
          this.isDrawingMode = false;
          this.currentDrawingCoordinates = [];
          this.drawingShape = null;
          this.hideMeasurementPopup();
        }

        this.logEvent(e);
      });

      this.map.on("gm:globaleditmodetoggled", (e) => {
        this.isAnyGeomanModeActive = e.enabled;
        this.logEvent(e);
      });

      this.map.on("gm:globalremovemodetoggled", (e) => {
        this.isAnyGeomanModeActive = e.enabled;
        this.logEvent(e);
      });

      this.map.on("gm:globalrotatemodetoggled", (e) => {
        this.isAnyGeomanModeActive = e.enabled;
        this.logEvent(e);
      });

      this.map.on("gm:globaldragmodetoggled", (e) => {
        this.isAnyGeomanModeActive = e.enabled;
        this.logEvent(e);
      });

      this.map.on("gm:globalcutmodetoggled", (e) => {
        this.isAnyGeomanModeActive = e.enabled;
        this.logEvent(e);
      });

      this.map.on("gm:create", (e) => {
        this.isDrawingMode = false;
        this.currentDrawingCoordinates = [];
        this.drawingShape = null;
        this.logEvent(e);
        this.handleMeasurementForFeature(e);
      });

      this.map.on("gm:editstart", (e) => {
        this.logEvent(e);
        this.hideMeasurementPopup();
      });

      this.map.on("gm:editend", (e) => {
        this.logEvent(e);
        this.handleMeasurementForFeature(e);
      });

      this.map.on("gm:remove", (e) => {
        this.logEvent(e);
        this.hideMeasurementPopup();
      });

      this.map.on("gm:dragstart", (e) => {
        this.logEvent(e);
        this.hideMeasurementPopup();
      });

      this.map.on("gm:dragend", (e) => {
        this.logEvent(e);
        this.handleMeasurementForFeature(e);
      });
    },

    /**
     * Clear hovered feature state
     */
    clearHover() {
      if (this.hoveredFeatureId !== null) {
        this.map.setFeatureState(
          {
            source: "protomaps",
            sourceLayer: "DAK_Parcel_Data_ENHANCED",
            id: this.hoveredFeatureId,
          },
          { hover: false }
        );
        this.hoveredFeatureId = null;
        this.hoveredFeature = null;
        this.map.getCanvas().style.cursor = "";
      }
    },

    /**
     * Clear all selected features
     */
    clearAllSelections() {
      for (const id of this.selectedFeatureIds) {
        this.map.setFeatureState(
          {
            source: "protomaps",
            sourceLayer: "DAK_Parcel_Data_ENHANCED",
            id: id,
          },
          { selected: false }
        );
      }
      this.selectedFeatureIds.clear();
      this.selectedFeatures = [];
    },

    /**
     * Log Geoman events to the sidebar
     */
    logEvent(e) {
      const eventData = {
        id: e.feature?.id || Date.now(),
        timestamp: new Date().toISOString(),
        type: e.type,
        shape: e.shape,
        enabled: e.enabled,
      };

      // Extract GeoJSON for create events
      if (
        e.type === "gm:create" &&
        e.feature?.source?.sourceInstance?._data?.features
      ) {
        const features = e.feature.source.sourceInstance._data.features;
        if (features.length > 0) {
          eventData.geojson = JSON.stringify(
            features[features.length - 1],
            null,
            2
          );
        }
      }

      this.gmEvents.unshift(eventData);
    },

    /**
     * Toggle GeoJSON display for an event
     */
    toggleGeoJson(index) {
      this.expandedGeoJsonIndex =
        this.expandedGeoJsonIndex === index ? -1 : index;
    },

    /**
     * Format distance in meters or kilometers
     */
    formatDistance(meters) {
      if (meters < 1000) {
        return `${meters.toFixed(2)} m`;
      }
      return `${(meters / 1000).toFixed(2)} km`;
    },

    /**
     * Format area in square meters or hectares
     */
    formatArea(squareMeters) {
      if (squareMeters < 10000) {
        return `${squareMeters.toFixed(2)} m²`;
      }
      return `${(squareMeters / 10000).toFixed(2)} ha`;
    },

    /**
     * Show measurement popup for a feature
     */
    showMeasurementPopup(feature, lngLat) {
      let measurement = "";

      if (feature.geometry.type === "LineString") {
        const distance = turf.length(feature, { units: "meters" });
        measurement = `Distance: ${this.formatDistance(distance)}`;
      } else if (feature.geometry.type === "Polygon") {
        const area = turf.area(feature);
        const perimeter = turf.length(turf.polygonToLine(feature), {
          units: "meters",
        });
        measurement = `Area: ${this.formatArea(
          area
        )}<br/>Perimeter: ${this.formatDistance(perimeter)}`;
      }

      if (measurement) {
        this.hideMeasurementPopup();
        this.measurementPopup = new maplibregl.Popup({
          closeButton: false,
          closeOnClick: false,
          className: "measurement-popup",
        })
          .setLngLat(lngLat)
          .setHTML(
            `<div style="font-size: 12px; padding: 4px;">${measurement}</div>`
          )
          .addTo(this.map);
      }
    },

    /**
     * Hide measurement popup
     */
    hideMeasurementPopup() {
      if (this.measurementPopup) {
        this.measurementPopup.remove();
        this.measurementPopup = null;
      }
    },

    /**
     * Show live measurements while drawing
     */
    showLiveDrawingMeasurement(mouseCoords) {
      if (!this.isDrawingMode || this.currentDrawingCoordinates.length === 0)
        return;

      const coords = [...this.currentDrawingCoordinates, mouseCoords];
      let measurement = "";

      if (this.drawingShape === "line" || this.drawingShape === "Line") {
        if (coords.length >= 2) {
          const lineFeature = {
            type: "Feature",
            properties: {},
            geometry: {
              type: "LineString",
              coordinates: coords,
            },
          };
          const distance = turf.length(lineFeature, { units: "meters" });
          measurement = `Distance: ${this.formatDistance(distance)}`;
        }
      } else if (
        this.drawingShape === "polygon" ||
        this.drawingShape === "Polygon"
      ) {
        if (coords.length >= 3) {
          const closedCoords = [...coords, coords[0]];
          const polygonFeature = {
            type: "Feature",
            properties: {},
            geometry: {
              type: "Polygon",
              coordinates: [closedCoords],
            },
          };
          const area = turf.area(polygonFeature);
          const perimeter = turf.length(turf.polygonToLine(polygonFeature), {
            units: "meters",
          });
          measurement = `Area: ${this.formatArea(
            area
          )}<br/>Perimeter: ${this.formatDistance(perimeter)}`;
        } else if (coords.length >= 2) {
          const lineFeature = {
            type: "Feature",
            properties: {},
            geometry: {
              type: "LineString",
              coordinates: coords,
            },
          };
          const distance = turf.length(lineFeature, { units: "meters" });
          measurement = `Distance: ${this.formatDistance(distance)}`;
        }
      }

      if (measurement) {
        this.hideMeasurementPopup();
        this.measurementPopup = new maplibregl.Popup({
          closeButton: false,
          closeOnClick: false,
          className: "measurement-popup",
        })
          .setLngLat(mouseCoords)
          .setHTML(
            `<div style="font-size: 12px; padding: 4px;">${measurement}</div>`
          )
          .addTo(this.map);
      }
    },

    /**
     * Handle measurements for completed features
     */
    handleMeasurementForFeature(e) {
      if (e.feature?.source?.sourceInstance?._data?.features) {
        const features = e.feature.source.sourceInstance._data.features;
        if (features.length > 0) {
          const feature = features[features.length - 1];
          if (
            feature.geometry.type === "LineString" ||
            feature.geometry.type === "Polygon"
          ) {
            const coords = feature.geometry.coordinates;
            let lngLat;

            if (feature.geometry.type === "LineString") {
              lngLat = coords[coords.length - 1];
            } else {
              const center = turf.centroid(feature);
              lngLat = center.geometry.coordinates;
            }

            this.showMeasurementPopup(feature, lngLat);
          }
        }
      }
    },

    /**
     * Check for plat query parameter and center map
     */
    checkPlatQueryParam() {
      const urlParams = new URLSearchParams(window.location.search);
      const platParam = urlParams.get("plat");
      if (platParam) {
        this.searchAndCenterOnPlat(platParam);
      }
    },

    /**
     * Search for parcels by plat value and center map
     */
    searchAndCenterOnPlat(platValue) {
      if (!this.map.isStyleLoaded()) {
        this.map.on("styledata", () => {
          this.searchAndCenterOnPlat(platValue);
        });
        return;
      }

      const features = this.map.querySourceFeatures("protomaps", {
        sourceLayer: "DAK_Parcel_Data_ENHANCED",
      });

      const matchingFeatures = features.filter(
        (feature) => feature.properties?.Plat === platValue
      );

      if (matchingFeatures.length > 0) {
        const bounds = new maplibregl.LngLatBounds();

        for (const feature of matchingFeatures) {
          if (feature.geometry.type === "Polygon") {
            for (const coord of feature.geometry.coordinates[0]) {
              bounds.extend(coord);
            }
          } else if (feature.geometry.type === "MultiPolygon") {
            for (const polygon of feature.geometry.coordinates) {
              for (const coord of polygon[0]) {
                bounds.extend(coord);
              }
            }
          }
        }

        this.map.fitBounds(bounds, {
          padding: 50,
          zoom: 16,
        });
      } else {
        console.warn(`No features found with plat value: ${platValue}`);
      }
    },

    /**
     * Save covenant - integrate with Django backend
     */
    saveCovenant() {
      console.log("Save covenant clicked");
      console.log("Selected features:", this.selectedFeatures);
      console.log("Events:", this.gmEvents);

      // Example Django integration:
      fetch("/api/save-covenant/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({
          selected_features: this.selectedFeatures,
          events: this.gmEvents,
        }),
      })
        .then((response) => response.json())
        .then((data) => {
          console.log("Success:", data);
          alert("Covenant saved successfully!");
        })
        .catch((error) => {
          console.error("Error:", error);
          alert("Error saving covenant");
        });
    },
  };
}

/**
 * Helper function to get CSRF token for Django
 */
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
