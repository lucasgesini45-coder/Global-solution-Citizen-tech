import React from "react";
import { View } from "react-native";
import WebView from "react-native-webview";

type Props = { url: string; trajeto?: number[][] };
export default function MapaPreview({ url, trajeto }: Props) {
  const pontos = (trajeto || []).filter(p => p.length === 2 && p.every(Number.isFinite));
  const dados = JSON.stringify(pontos).replace(/</g, "\\u003c");
  const html = `<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"/><link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/><style>html,body,#map{height:100%;width:100%;margin:0}</style></head><body><div id="map"></div><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><script>const pts=${dados};const m=L.map('map');L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; OpenStreetMap contributors'}).addTo(m);const p=L.polyline(pts,{color:'#655be8',weight:6}).addTo(m);L.circleMarker(pts[0],{radius:8,color:'#216af0',fillOpacity:1}).addTo(m);L.circleMarker(pts[pts.length-1],{radius:8,color:'#8a37d6',fillOpacity:1}).addTo(m);m.fitBounds(p.getBounds().pad(.28));</script></body></html>`;
  return <View style={{ height: 330, borderRadius: 14, overflow: "hidden" }}>
    <WebView originWhitelist={["*"]} source={pontos.length ? { html, baseUrl: "https://localhost/" } : { uri: url }} style={{ flex: 1 }} />
  </View>;
}
