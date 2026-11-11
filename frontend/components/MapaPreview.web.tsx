import React from "react";
import { View } from "react-native";

type Props = {
  url: string;
  trajeto?: number[][];
  pontos?: {lat:number;lon:number;nome?:string}[];
};
const key = process.env.EXPO_PUBLIC_CARTO_KEY || "";

export default function MapaPreview({ url, trajeto, pontos=[] }: Props) {
  const rota = (trajeto || []).filter(p=>p.length===2&&p.every(Number.isFinite));
  const marcas = pontos.filter(p=>Number.isFinite(p.lat)&&Number.isFinite(p.lon));
  const payload = JSON.stringify({rota,marcas}).replace(/</g,"\\u003c");
  const carto = JSON.stringify(key);
  const html = `<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1" />
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>html,body,#map{height:100%;width:100%;margin:0;background:#e8edf3} .leaflet-control-attribution{font:10px system-ui!important} .leaflet-container{font-family:system-ui}</style></head><body><div id="map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const v=${payload}, key=${carto}, map=L.map("map",{zoomControl:true}).setView([-23.55,-46.63],12);
const tiles=key?"https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png?key="+encodeURIComponent(key):"https://tile.openstreetmap.org/{z}/{x}/{y}.png";
L.tileLayer(tiles,{maxZoom:19,attribution:key?'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="https://carto.com/attribution/">CARTO</a>':'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'}).addTo(map);
const bounds=[];
if(v.rota.length){
  const line=L.polyline(v.rota,{color:"#5266e7",weight:7,opacity:.92,lineJoin:"round"}).addTo(map);
  line.bringToFront();bounds.push(...v.rota);
  [v.rota[0],v.rota[v.rota.length-1]].forEach((p,i)=>L.circleMarker(p,{radius:9,weight:3,color:"#fff",fillColor:i?"#8b50d3":"#246cf0",fillOpacity:1}).addTo(map));
}
for(const p of v.marcas){
 const xy=[p.lat,p.lon];bounds.push(xy);
 L.circleMarker(xy,{radius:8,color:"#fff",weight:3,fillColor:"#7262cf",fillOpacity:1}).bindPopup(p.nome||"Endereço selecionado").addTo(map);
}
if(bounds.length===1)map.setView(bounds[0],15); else if(bounds.length>1)map.fitBounds(bounds,{padding:[28,28],maxZoom:16});
</script></body></html>`;
  return <View style={{height:365,width:"100%",borderRadius:12,overflow:"hidden"}}>
    {React.createElement("iframe",{srcDoc:html,title:"Mapa interativo com endereços e rotas",style:{width:"100%",height:"100%",border:0},loading:"lazy"})}
  </View>;
}
