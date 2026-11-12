import React from "react";
import { View } from "react-native";

type Ponto = {lat:number;lon:number;nome?:string;tipo?:string};
type Props = {url:string;trajeto?:number[][];pontos?:Ponto[];height?:number};

/** Mapa de ruas do navegador: somente marcadores, sem linhas sobrepostas. */
export default function MapaPreview({pontos=[],height=365}:Props) {
 const marcas=pontos.filter(p=>Number.isFinite(p.lat)&&Number.isFinite(p.lon));
 const payload=JSON.stringify({marcas}).replace(/</g,"\\u003c");
 const html=`<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
 <meta name="viewport" content="width=device-width,initial-scale=1">
 <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
 <style>
 html,body,#map{margin:0;width:100%;height:100%;background:#eff5fb;font-family:Inter,system-ui,sans-serif}
 .leaflet-control-zoom{border:0!important;border-radius:13px!important;overflow:hidden;box-shadow:0 3px 15px rgba(51,97,145,.15)!important}
 .leaflet-control-zoom a{color:#0069d2!important;background:#fff!important}
 .leaflet-control-attribution{font:10px system-ui!important;background:rgba(255,255,255,.88)!important}
 .pin{width:29px;height:29px;border:3px solid #fff;border-radius:50%;box-sizing:border-box;display:flex;justify-content:center;align-items:center;color:#fff;font-size:12px;font-weight:800;box-shadow:0 3px 10px rgba(26,75,127,.25)}
 .pin.start{background:#0071e3}.pin.end{background:#405fc7}
 .map-tag{position:absolute;top:15px;left:15px;z-index:900;background:rgba(255,255,255,.96);border-radius:12px;padding:9px 12px;box-shadow:0 3px 12px rgba(51,97,145,.12);color:#37516b;font:600 12px system-ui;pointer-events:none}
 .leaflet-popup-content-wrapper{border-radius:12px}
 </style></head><body><div id="map"></div><div class="map-tag">Mapa de ruas · São Paulo e região</div>
 <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
 <script>
 const data=${payload},map=L.map("map",{zoomControl:false,scrollWheelZoom:true}).setView([-23.5505,-46.6333],13);
 L.control.zoom({position:"topright"}).addTo(map);
 L.tileLayer("https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",{maxZoom:19,subdomains:"abcd",attribution:'&copy; OpenStreetMap contributors &copy; CARTO'}).addTo(map);
 const bounds=[];
 data.marcas.forEach(function(p,i){
   const pos=[p.lat,p.lon];bounds.push(pos);
   const tipo=p.tipo==="destino"?"end":"start";
   const letra=tipo==="end"?"B":"A";
   const ic=L.divIcon({className:"",html:'<div class="pin '+tipo+'">'+letra+'</div>',iconSize:[30,30],iconAnchor:[15,15]});
   L.marker(pos,{icon:ic}).addTo(map).bindPopup(String(p.nome||"Endereço"));
 });
 if(bounds.length===1)map.setView(bounds[0],15);
 else if(bounds.length>1)map.fitBounds(bounds,{padding:[48,48],maxZoom:16});
 setTimeout(()=>map.invalidateSize(),180);
 </script></body></html>`;
 return <View style={{height,width:"100%",borderRadius:18,overflow:"hidden",backgroundColor:"#eff5fb"}}>
  {React.createElement("iframe",{srcDoc:html,title:"Mapa interativo de ruas com origem e destino",style:{width:"100%",height:"100%",border:0},loading:"eager"})}
 </View>;
}
