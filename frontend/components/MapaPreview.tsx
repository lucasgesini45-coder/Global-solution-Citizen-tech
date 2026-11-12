import React from "react";
import { View } from "react-native";
import WebView from "react-native-webview";

type Ponto = {lat:number;lon:number;nome?:string;tipo?:string};
type Props = {url:string;trajeto?:number[][];pontos?:Ponto[];height?:number};

/**
 * Mapa real com identidade visual inspirada no painel Figma.
 * Exibe ruas reais e os pontos selecionados, sem sobrepor linhas de rotas.
 */
export default function MapaPreview({trajeto,pontos=[],height=365}:Props){
 const marcas=pontos.filter(p=>Number.isFinite(p.lat)&&Number.isFinite(p.lon));
 const dados=JSON.stringify({marcas}).replace(/</g,"\\u003c");
 const html=`<!doctype html><html lang="pt-BR"><head>
 <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
 <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
 <style>
 html,body,#map{height:100%;width:100%;margin:0;background:#eff5fb;font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif}
 .leaflet-container{background:#eff5fb}
 .leaflet-control-attribution{background:rgba(255,255,255,.88)!important;color:#71869c!important;font-size:10px!important}
 .leaflet-control-attribution a{color:#436d9a!important}
 .leaflet-control-zoom{border:0!important;box-shadow:0 4px 16px rgba(51,97,145,.12)!important;border-radius:13px!important;overflow:hidden}
 .leaflet-control-zoom a{width:38px!important;height:38px!important;line-height:38px!important;color:#1d4f8e!important;background:#fff!important;border:0!important;font-size:20px!important}
 .leaflet-control-zoom a:first-child{border-bottom:1px solid #e5edf5!important}
 .leaflet-control-zoom a:hover{background:#eff6ff!important}
 .leaflet-bar a.leaflet-disabled{color:#aab7c5!important}
 .leaflet-popup-content-wrapper{background:#fff;border-radius:14px;box-shadow:0 6px 22px rgba(51,97,145,.18);color:#1d2633}
 .leaflet-popup-content{margin:11px 15px;font-size:12px;font-weight:600}
 .leaflet-popup-tip{box-shadow:none}
 .badge-pin{display:flex;align-items:center;justify-content:center;border:3px solid white;box-shadow:0 3px 10px rgba(26,75,127,.28);border-radius:50%;width:29px;height:29px;font-weight:800;color:#fff;font-size:13px}
 .badge-pin.start{background:#0071e3}.badge-pin.end{background:#405fc7}
 .map-chip{position:absolute;top:15px;left:15px;z-index:1000;pointer-events:none;background:rgba(255,255,255,.96);border:1px solid #e0eaf3;border-radius:13px;padding:10px 13px;box-shadow:0 4px 16px rgba(51,97,145,.09);font-size:12px;color:#37516b;font-weight:700;display:flex;align-items:center;gap:8px}
 .map-chip-dot{width:9px;height:9px;background:#0071e3;border-radius:50%}
 .layer-button{position:absolute;top:15px;right:15px;z-index:1001;border:0;border-radius:13px;background:#fff;box-shadow:0 4px 16px rgba(51,97,145,.12);padding:11px 13px;color:#1d4f8e;font:600 12px Inter,Arial,sans-serif;cursor:pointer}
 .layer-button:focus-visible{outline:2px solid #0071e3;outline-offset:3px}
 .leaflet-top.leaflet-right{top:51px;right:4px}
 </style></head><body>
 <div id="map" role="application" aria-label="Mapa interativo da rota"></div>
 <div class="map-chip"><span class="map-chip-dot"></span><span id="mapstatus">São Paulo e região</span></div>
 <button id="layers" class="layer-button" aria-label="Alternar estilo do mapa" type="button">▤ Camadas</button>
 <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
 <script>
 (function(){
  const dados=${dados};
  const mapa=L.map("map",{zoomControl:false,scrollWheelZoom:true}).setView([-23.5505,-46.6333],13);
  L.control.zoom({position:"topright",zoomInTitle:"Aproximar",zoomOutTitle:"Afastar"}).addTo(mapa);
  const carto=L.tileLayer("https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",{maxZoom:19,attribution:'&copy; OpenStreetMap contributors &copy; CARTO',subdomains:"abcd"});
  const osm=L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:19,attribution:'&copy; OpenStreetMap contributors'});
  let claro=true;carto.addTo(mapa);
  document.getElementById("layers").addEventListener("click",function(){
   mapa.removeLayer(claro?carto:osm);(claro?osm:carto).addTo(mapa);claro=!claro;
   this.textContent=claro?"▤ Camadas · claro":"▤ Camadas · ruas";
  });
  const area=[];
  dados.marcas.forEach(function(p,i){
   const latlng=[p.lat,p.lon];area.push(latlng);
   const classe=p.tipo==="destino"?"end":"start";
   const texto=String(p.nome|| (i===0?"Origem":"Destino"));
   const icon=L.divIcon({className:"",iconSize:[32,32],iconAnchor:[16,16],
    html:'<div class="badge-pin '+classe+'">'+(classe==="end"?"B":"A")+'</div>'});
   const marker=L.marker(latlng,{icon:icon}).addTo(mapa).bindPopup(texto);
   if(i===0)marker.setZIndexOffset(100);
  });
  if(area.length===1)mapa.setView(area[0],15);
  else if(area.length>1)mapa.fitBounds(area,{padding:[70,70],maxZoom:16});
  setTimeout(function(){mapa.invalidateSize();},250);
 })();
 </script></body></html>`;
 return <View style={{height,borderRadius:18,overflow:"hidden",backgroundColor:"#eff5fb"}}>
   <WebView originWhitelist={["*"]} source={{html,baseUrl:"https://localhost/"}} style={{flex:1}} javaScriptEnabled domStorageEnabled/>
 </View>;
}
