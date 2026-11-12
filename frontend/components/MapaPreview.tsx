import React from "react";
import { View } from "react-native";
import WebView from "react-native-webview";

type Props = {url:string;trajeto?:number[][];pontos?:{lat:number;lon:number;nome?:string}[];height?:number};
const key=process.env.EXPO_PUBLIC_CARTO_KEY || "";
export default function MapaPreview({trajeto,pontos=[],height=365}:Props){
 const rota=(trajeto||[]).filter(p=>p.length===2&&p.every(Number.isFinite));
 const marcas=pontos.filter(p=>Number.isFinite(p.lat)&&Number.isFinite(p.lon));
 const dados=JSON.stringify({rota,marcas}).replace(/</g,"\\u003c");
 const html=`<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1" /><link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/><style>html,body,#map{height:100%;width:100%;margin:0}</style></head><body><div id="map"></div><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><script>
 const v=${dados},k=${JSON.stringify(key)},m=L.map("map").setView([-23.55,-46.63],12);
 L.tileLayer(k?"https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png?key="+encodeURIComponent(k):"https://tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:19,attribution:k?'&copy; OpenStreetMap contributors, &copy; CARTO':'&copy; OpenStreetMap contributors'}).addTo(m);
 const b=[];
 if(v.rota.length){L.polyline(v.rota,{color:"#5266e7",weight:6}).addTo(m);b.push(...v.rota);[v.rota[0],v.rota[v.rota.length-1]].forEach((p,i)=>L.circleMarker(p,{radius:8,color:"#fff",weight:3,fillColor:i?"#8b50d3":"#246cf0",fillOpacity:1}).addTo(m));}
 v.marcas.forEach(p=>{let x=[p.lat,p.lon];b.push(x);L.circleMarker(x,{radius:8,color:"#fff",weight:3,fillColor:"#7262cf",fillOpacity:1}).bindPopup(p.nome||"Endereço").addTo(m)});
 if(b.length===1)m.setView(b[0],15);else if(b.length>1)m.fitBounds(b,{padding:[28,28],maxZoom:16});
 </script></body></html>`;
 return <View style={{height,borderRadius:18,overflow:"hidden"}}><WebView originWhitelist={["*"]} source={{html,baseUrl:"https://localhost/"}} style={{flex:1}}/></View>;
}
