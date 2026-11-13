import React, { useEffect, useRef, useState } from "react";
import { Text, View } from "react-native";

type Ponto = {lat:number;lon:number;nome?:string;tipo?:string};
type Trecho = {modal:string;trajeto:number[][];linha?:string|null;cor_linha?:string|null;paradas?:{nome:string;lat:number;lon:number}[]};
type Props = {url:string;trajeto?:number[][];trechos?:Trecho[];pontos?:Ponto[];height?:number;pickMode?:"origem"|"destino"|null;onMapPick?:(lat:number,lon:number)=>void};

type MapLibreApi = {
 Map: new (options: Record<string, unknown>) => any;
 Marker: new (options: Record<string, unknown>) => any;
 Popup: new (options: Record<string, unknown>) => any;
 NavigationControl: new (options: Record<string, unknown>) => any;
 LngLatBounds: new () => any;
};

const SCRIPT_ID = "citizen-maplibre-script";
const CSS_ID = "citizen-maplibre-css";
const SCRIPT_URL = "https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js";
const CSS_URL = "https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css";
const STYLE_URL = "https://tiles.openfreemap.org/styles/positron";

function getMapLibre(): MapLibreApi | undefined {
 return (window as unknown as {maplibregl?:MapLibreApi}).maplibregl;
}

let loadingScript: Promise<MapLibreApi> | null = null;
function loadMapLibre(): Promise<MapLibreApi> {
 const loaded = getMapLibre();
 if (loaded) return Promise.resolve(loaded);
 if (loadingScript) return loadingScript;
 loadingScript = new Promise<MapLibreApi>((resolve,reject)=>{
   if (!document.getElementById(CSS_ID)) {
     const css=document.createElement("link");css.id=CSS_ID;css.rel="stylesheet";css.href=CSS_URL;
     document.head.appendChild(css);
   }
   const finish=()=>{const lib=getMapLibre();lib?resolve(lib):reject(new Error("Biblioteca de mapas não carregada."));};
   let script=document.getElementById(SCRIPT_ID) as HTMLScriptElement|null;
   if (!script) {
     script=document.createElement("script");
     script.id=SCRIPT_ID;
     script.src=SCRIPT_URL;
     script.async=true;
     script.onload=finish;
     script.onerror=()=>reject(new Error("Não foi possível baixar a biblioteca MapLibre."));
     document.head.appendChild(script);
   } else {
     script.addEventListener("load",finish,{once:true});
     script.addEventListener("error",()=>reject(new Error("Não foi possível baixar a biblioteca MapLibre.")),{once:true});
   }
 });
 loadingScript.catch(()=>{loadingScript=null;document.getElementById(SCRIPT_ID)?.remove();});
 return loadingScript;
}

/** Usa DOM direto no Expo Web: MapLibre não funciona com segurança em iframe srcDoc. */
export default function MapaPreview({pontos=[],height=365,trajeto=[],trechos=[],pickMode=null,onMapPick}:Props) {
 const containerRef=useRef<HTMLDivElement|null>(null);
 const mapRef=useRef<any>(null);
 const markersRef=useRef<any[]>([]);
 const pickModeRef=useRef(pickMode);
 const onMapPickRef=useRef(onMapPick);
 pickModeRef.current=pickMode;
 onMapPickRef.current=onMapPick;
 const [erro,setErro]=useState("");
 const [pronto,setPronto]=useState(false);
 const marcas=pontos.filter(p=>Number.isFinite(p.lat)&&Number.isFinite(p.lon));
 const marcadores=JSON.stringify(marcas.map(p=>({lat:p.lat,lon:p.lon,nome:p.nome,tipo:p.tipo})));
 const linhas=JSON.stringify(trechos.length?trechos:[{modal:"WALK",trajeto}]);

 useEffect(()=>{
   let active=true;
   let timeout:ReturnType<typeof setTimeout>|null=null;
   setErro("");setPronto(false);
   loadMapLibre().then(lib=>{
     if(!active||!containerRef.current)return;
     if(!lib.Map || !lib.Marker)throw new Error("Biblioteca MapLibre incompleta.");
     const map=new lib.Map({
       container:containerRef.current,
       style:STYLE_URL,
       center:[-46.6333,-23.5505],
       zoom:12.5,
       attributionControl:true
     });
     mapRef.current=map;
     map.addControl(new lib.NavigationControl({showCompass:false}),"top-right");
     map.on("click",(event:{lngLat:{lat:number;lng:number}})=>{
       if(pickModeRef.current&&onMapPickRef.current){
         onMapPickRef.current(event.lngLat.lat,event.lngLat.lng);
       }
     });
     map.on("load",()=>{
       if(!active)return;
       setPronto(true);setErro("");
       map.resize();
     });
     map.on("error",(event:{error?:{message?:string}})=>{
       if(active&&!map.loaded())setErro("Falha ao carregar o Positron. Confira sua conexão e o acesso ao OpenFreeMap. "+(event?.error?.message||""));
     });
     timeout=setTimeout(()=>{
       if(active&&!map.loaded())setErro("O mapa não carregou. Confira no navegador se o OpenFreeMap e o MapLibre estão acessíveis.");
     },12000);
   }).catch(e=>{if(active)setErro(e instanceof Error?e.message:"Erro ao iniciar o mapa.");});
   return ()=>{
     active=false;
     if(timeout)clearTimeout(timeout);
     markersRef.current.forEach(marker=>marker.remove());markersRef.current=[];
     mapRef.current?.remove();mapRef.current=null;
   };
 },[]);

 useEffect(()=>{
   if(!pronto||!mapRef.current)return;
   let cancelled=false;
   loadMapLibre().then(lib=>{
     if(cancelled||!mapRef.current)return;
     markersRef.current.forEach(marker=>marker.remove());markersRef.current=[];
     const bounds=new lib.LngLatBounds();
     const lista=JSON.parse(marcadores) as Ponto[];
     lista.forEach(p=>{
       const destino=p.tipo==="destino";
       const el=document.createElement("div");
       el.textContent=destino?"B":"A";
       Object.assign(el.style,{
         display:"flex",alignItems:"center",justifyContent:"center",
         width:"30px",height:"30px",boxSizing:"border-box",border:"3px solid white",
         borderRadius:"50%",background:destino?"#405fc7":"#0071e3",
         color:"#fff",fontSize:"12px",fontWeight:"800",boxShadow:"0 3px 9px rgba(25,74,135,.27)"
       });
       const marker=new lib.Marker({element:el,anchor:"center"})
         .setLngLat([p.lon,p.lat])
         .setPopup(new lib.Popup({offset:18}).setText(p.nome||(destino?"Destino":"Origem")))
         .addTo(mapRef.current);
       markersRef.current.push(marker);
       bounds.extend([p.lon,p.lat]);
     });
     if(!mapRef.current.getSource("citizen-route")){
       if(lista.length===1)mapRef.current.jumpTo({center:bounds.getCenter(),zoom:15});
       else if(lista.length>1)mapRef.current.fitBounds(bounds,{padding:65,maxZoom:16,duration:0});
     }
     mapRef.current.resize();
   }).catch(e=>{if(!cancelled)setErro(e instanceof Error?e.message:"Falha ao marcar endereços.");});
   return ()=>{cancelled=true;};
 },[marcadores,pronto]);

 useEffect(()=>{
   const map=mapRef.current;
   if(!pronto||!map)return;
   const id="citizen-route";
   const lista=JSON.parse(linhas) as Trecho[];
   const cores:Record<string,string>={WALK:"#2596a9",BUS:"#0071e3",SUBWAY:"#7155c8",SUBURBAN:"#7155c8",REGIONAL_RAIL:"#7155c8",RAIL:"#7155c8",TRAM:"#7155c8"};
   const features=lista.filter(t=>Array.isArray(t.trajeto)&&t.trajeto.length>=2).map((t,i)=>({
     type:"Feature",properties:{cor:t.cor_linha||cores[t.modal]||"#7155c8",modo:t.modal,linha:t.linha||"",index:i},
     geometry:{type:"LineString",coordinates:t.trajeto.filter(p=>Array.isArray(p)&&p.length===2&&p.every(Number.isFinite)).map(p=>[p[1],p[0]])}
   })).filter(f=>f.geometry.coordinates.length>=2);
   if(map.getLayer(id+"-stations-labels"))map.removeLayer(id+"-stations-labels");
   if(map.getLayer(id+"-stations"))map.removeLayer(id+"-stations");
   if(map.getSource(id+"-stations"))map.removeSource(id+"-stations");
   if(map.getLayer(id+"-stroke"))map.removeLayer(id+"-stroke");
   if(map.getLayer(id+"-line"))map.removeLayer(id+"-line");
   if(map.getSource(id))map.removeSource(id);
   if(!features.length)return;
   map.addSource(id,{type:"geojson",data:{type:"FeatureCollection",features}});
   map.addLayer({id:id+"-stroke",type:"line",source:id,paint:{"line-color":"#ffffff","line-width":9,"line-opacity":0.9},layout:{"line-join":"round","line-cap":"round"}});
   map.addLayer({id:id+"-line",type:"line",source:id,paint:{"line-color":["get","cor"],"line-width":5,"line-opacity":0.95},layout:{"line-join":"round","line-cap":"round"}});
   const pontos=lista.flatMap(t=>(t.paradas||[]).map(p=>({type:"Feature",properties:{nome:p.nome,modal:t.modal,cor:t.cor_linha||cores[t.modal]||"#7155c8"},geometry:{type:"Point",coordinates:[p.lon,p.lat]}}))).filter(f=>f.geometry.coordinates.every(Number.isFinite));
   if(pontos.length){
     map.addSource(id+"-stations",{type:"geojson",data:{type:"FeatureCollection",features:pontos}});
     map.addLayer({id:id+"-stations",type:"circle",source:id+"-stations",paint:{"circle-radius":5,"circle-color":["get","cor"],"circle-stroke-width":2,"circle-stroke-color":"#fff"}});
     map.addLayer({id:id+"-stations-labels",type:"symbol",source:id+"-stations",layout:{"text-field":["get","nome"],"text-size":11,"text-offset":[0,1.1],"text-anchor":"top","text-optional":true},paint:{"text-color":"#244263","text-halo-color":"#fff","text-halo-width":1.5}});
   }
   const bounds=new (getMapLibre()!).LngLatBounds();
   features.forEach(f=>f.geometry.coordinates.forEach(p=>bounds.extend(p)));
   if(!bounds.isEmpty())map.fitBounds(bounds,{padding:65,maxZoom:16,duration:450});
 },[linhas,pronto]);

 return <View style={{height,width:"100%",borderRadius:18,overflow:"hidden",backgroundColor:"#eff3f7",position:"relative"}}>
   {React.createElement("div",{
     ref:containerRef,
     "aria-label":"Mapa OpenFreeMap Positron",
     style:{width:"100%",height:"100%",cursor:pickMode?"crosshair":"grab"}
   })}
   <View pointerEvents="none" style={{position:"absolute",top:15,left:15,backgroundColor:"rgba(255,255,255,.95)",paddingHorizontal:12,paddingVertical:9,borderRadius:12}}>
     <Text style={{color:"#37516b",fontWeight:"700",fontSize:12}}>OpenFreeMap · Positron</Text>
   </View>
   {!!pickMode&&<View pointerEvents="none" style={{position:"absolute",left:14,right:14,bottom:18,backgroundColor:"#e8f3ff",padding:12,borderRadius:10,borderWidth:1,borderColor:"#afcdf0"}}><Text style={{color:"#12568c",fontSize:12,fontWeight:"700"}}>{"Clique no mapa para marcar "+(pickMode==="origem"?"a origem":"o destino")}</Text></View>}
   {!!erro&&<View style={{position:"absolute",left:14,right:14,bottom:18,backgroundColor:"#fff4e9",padding:12,borderRadius:10,borderWidth:1,borderColor:"#f3d4b6"}}>
      <Text style={{color:"#8f4e22",fontSize:12}}>{erro}</Text>
   </View>}
 </View>;
}
