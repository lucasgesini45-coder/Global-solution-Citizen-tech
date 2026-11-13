import React from "react";
import { View } from "react-native";
import WebView from "react-native-webview";

type Ponto={lat:number;lon:number;nome?:string;tipo?:string};
type Trecho={modal:string;trajeto:number[][];linha?:string|null;cor_linha?:string|null;paradas?:{nome:string;lat:number;lon:number}[]};
type Props={url:string;trajeto?:number[][];trechos?:Trecho[];pontos?:Ponto[];height?:number;pickMode?:"origem"|"destino"|null;onMapPick?:(lat:number,lon:number)=>void};

export default function MapaPreview({pontos=[],height=365,trajeto=[],trechos=[],pickMode=null,onMapPick}:Props){
 const marcas=pontos.filter(p=>Number.isFinite(p.lat)&&Number.isFinite(p.lon));
 const payload=JSON.stringify({marcas}).replace(/</g,"\\u003c");
 const modo=JSON.stringify(pickMode);
 const linhas=JSON.stringify(trechos.length?trechos:[{modal:"WALK",trajeto}]).replace(/</g,"\\u003c");
 const html=`<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css">
<style>
html,body,#map{margin:0;width:100%;height:100%;background:#eff3f7;font-family:Inter,Arial,sans-serif}
.maplibregl-control-container .maplibregl-ctrl-top-right{top:48px;right:7px}
.maplibregl-ctrl-group{border-radius:12px!important;overflow:hidden;box-shadow:0 4px 16px rgba(51,97,145,.14)!important}
.maplibregl-ctrl-attrib{font-size:10px!important}
.pin{width:30px;height:30px;box-sizing:border-box;border:3px solid #fff;border-radius:50%;background:#0071e3;color:white;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:12px;box-shadow:0 3px 9px rgba(25,74,135,.27)}
.pin.end{background:#405fc7}
.legend{position:absolute;top:54px;left:15px;z-index:2;background:#fffffff2;border-radius:10px;padding:10px 12px;font-size:11px;font-weight:700;color:#244263;box-shadow:0 3px 12px #0001}.legend div{margin:4px 0}.legend b{display:inline-block;width:20px;height:4px;vertical-align:middle;margin-right:6px;border-radius:2px}
.tag{position:absolute;top:15px;left:15px;z-index:2;background:#fffffff0;color:#37516b;border-radius:12px;padding:10px 13px;font-weight:700;font-size:12px;box-shadow:0 4px 12px rgba(51,97,145,.12);pointer-events:none}
#error{display:none;position:absolute;left:12px;bottom:28px;right:12px;background:#fff4e9;color:#8f4e22;padding:11px;border-radius:10px;z-index:5;font-size:12px}
.maplibregl-popup-content{border-radius:12px;padding:12px;font-size:12px}
</style></head><body>
<div id="map" aria-label="Mapa interativo OpenFreeMap Positron"></div>
<div class="tag">OpenFreeMap · Positron</div><div id="legend" class="legend" style="display:none"></div><div id="error" role="alert"></div>
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
<script>
(function(){
 const data=${payload};
 const pickMode=${modo};
 const trechos=${linhas};
 const errorBox=document.getElementById("error");
 function showError(message){errorBox.textContent=message;errorBox.style.display="block";}
 if(!window.maplibregl){showError("Biblioteca do mapa indisponível. Verifique sua conexão.");return;}
 try {
  const map=new maplibregl.Map({container:"map",style:"https://tiles.openfreemap.org/styles/positron",center:[-46.6333,-23.5505],zoom:12.5,attributionControl:true});
  map.addControl(new maplibregl.NavigationControl({showCompass:false}),"top-right");
  map.on("click",function(event){
    if(pickMode && window.ReactNativeWebView){
      window.ReactNativeWebView.postMessage(JSON.stringify({type:"map_pick",lat:event.lngLat.lat,lon:event.lngLat.lng}));
    }
  });
  map.on("error",function(event){if(!map.loaded())showError("Não foi possível carregar o mapa. Verifique o acesso ao OpenFreeMap.");});
  map.on("load",function(){
   errorBox.style.display="none";
   const bounds=new maplibregl.LngLatBounds();
   data.marcas.forEach(function(p){
    if(!Number.isFinite(p.lat)||!Number.isFinite(p.lon))return;
    const isEnd=p.tipo==="destino";
    const pin=document.createElement("div");
    pin.className="pin"+(isEnd?" end":"");
    pin.textContent=isEnd?"B":"A";
    const popup=new maplibregl.Popup({offset:18}).setText(String(p.nome|| (isEnd?"Destino":"Origem")));
    new maplibregl.Marker({element:pin,anchor:"center"}).setLngLat([p.lon,p.lat]).setPopup(popup).addTo(map);
    bounds.extend([p.lon,p.lat]);
   });
   const cores={WALK:"#2596a9",BUS:"#0071e3",SUBWAY:"#7155c8",SUBURBAN:"#7155c8",REGIONAL_RAIL:"#7155c8",RAIL:"#7155c8",TRAM:"#7155c8"};
   const geometria=trechos.filter(t=>Array.isArray(t.trajeto)&&t.trajeto.length>=2).map(t=>({type:"Feature",properties:{cor:t.cor_linha||cores[t.modal]||"#7155c8",rotulo:t.modal==="WALK"?"A pé":t.modal==="BUS"?"Ônibus"+(t.linha?" · "+t.linha:""):"Metrô / trem"+(t.linha?" · "+t.linha:"")},geometry:{type:"LineString",coordinates:t.trajeto.filter(p=>Array.isArray(p)&&p.length===2&&p.every(Number.isFinite)).map(p=>[p[1],p[0]])}})).filter(t=>t.geometry.coordinates.length>=2);
   if(geometria.length){
     map.addSource("citizen-route",{type:"geojson",data:{type:"FeatureCollection",features:geometria}});
     map.addLayer({id:"citizen-route-outline",type:"line",source:"citizen-route",paint:{"line-color":"#fff","line-width":9},layout:{"line-join":"round","line-cap":"round"}});
     map.addLayer({id:"citizen-route-lines",type:"line",source:"citizen-route",paint:{"line-color":["get","cor"],"line-width":5},layout:{"line-join":"round","line-cap":"round"}});
     map.addLayer({id:"citizen-route-labels",type:"symbol",source:"citizen-route",layout:{"symbol-placement":"line","text-field":["get","rotulo"],"text-size":12,"symbol-spacing":190,"text-rotation-alignment":"map","text-keep-upright":true,"text-optional":true},paint:{"text-color":"#183e67","text-halo-color":"#fff","text-halo-width":2.5}});
     const legend=document.getElementById("legend");
     const tipos=[];
     trechos.forEach(function(t){const k=t.modal==="WALK"?"A pé":t.modal==="BUS"?"Ônibus":"Metrô / trem";if(!tipos.includes(k))tipos.push(k);});
     tipos.forEach(function(tipo){
       const item=document.createElement("div"),line=document.createElement("b");
       line.style.background=tipo==="A pé"?"#2596a9":tipo==="Ônibus"?"#0071e3":"#7155c8";
       item.appendChild(line);item.appendChild(document.createTextNode(tipo));legend.appendChild(item);
     });
     if(tipos.length)legend.style.display="block";
     const paradas=trechos.flatMap(t=>(t.paradas||[]).map(p=>({type:"Feature",properties:{nome:p.nome,cor:t.cor_linha||cores[t.modal]||"#7155c8"},geometry:{type:"Point",coordinates:[p.lon,p.lat]}}))).filter(p=>p.geometry.coordinates.every(Number.isFinite));
     if(paradas.length){
       map.addSource("citizen-stations",{type:"geojson",data:{type:"FeatureCollection",features:paradas}});
       map.addLayer({id:"citizen-stations-markers",type:"circle",source:"citizen-stations",paint:{"circle-radius":5,"circle-color":["get","cor"],"circle-stroke-color":"#fff","circle-stroke-width":2}});
       map.addLayer({id:"citizen-stations-names",type:"symbol",source:"citizen-stations",layout:{"text-field":["get","nome"],"text-size":11,"text-offset":[0,1.1],"text-anchor":"top","text-optional":true},paint:{"text-color":"#244263","text-halo-color":"#fff","text-halo-width":1.5}});
     }
     geometria.forEach(g=>g.geometry.coordinates.forEach(pos=>bounds.extend(pos)));
   }
   if(geometria.length&&!bounds.isEmpty())map.fitBounds(bounds,{padding:65,maxZoom:16,duration:0});
   else if(data.marcas.length===1&& !bounds.isEmpty())map.jumpTo({center:bounds.getCenter(),zoom:15});
   else if(data.marcas.length>1&& !bounds.isEmpty())map.fitBounds(bounds,{padding:65,maxZoom:16,duration:0});
   map.resize();
  });
 }catch(e){showError("Falha ao iniciar o mapa Positron.");}
})();
</script></body></html>`;
 return <View style={{height,width:"100%",borderRadius:18,overflow:"hidden",backgroundColor:"#eff3f7"}}>
   <WebView originWhitelist={["*"]} source={{html,baseUrl:"https://tiles.openfreemap.org/"}} style={{flex:1}} javaScriptEnabled domStorageEnabled onMessage={(event)=>{
     try{
       const msg=JSON.parse(event.nativeEvent.data);
       if(msg.type==="map_pick"&&Number.isFinite(msg.lat)&&Number.isFinite(msg.lon))onMapPick?.(msg.lat,msg.lon);
     }catch{/* mensagem não reconhecida */}
   }}/>
 </View>;
}
