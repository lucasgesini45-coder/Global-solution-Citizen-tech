export type Geo={lat:number;lon:number};
export type PosicaoGPS=Geo & {accuracy:number|null;timestamp:number};
export type EtapaGPS={modal:string;inicio_geo?:Geo|null;fim_geo?:Geo|null};
export type Evidencia={indice:number;inicioVisto:boolean;afastou:boolean;confirmacoes:number;ultimo:number};
export const novaEvidencia=(indice:number):Evidencia=>({indice,inicioVisto:false,afastou:false,confirmacoes:0,ultimo:0});
export function distancia(a:Geo,b:Geo){
 const r=Math.PI/180, dlat=(b.lat-a.lat)*r,dlon=(b.lon-a.lon)*r;
 const h=Math.sin(dlat/2)**2+Math.cos(a.lat*r)*Math.cos(b.lat*r)*Math.sin(dlon/2)**2;
 return 6371000*2*Math.asin(Math.sqrt(Math.min(1,Math.max(0,h))));
}
export function gpsValido(p:PosicaoGPS|null,agora=Date.now()){
 return !!p&&Number.isFinite(p.lat)&&Number.isFinite(p.lon)&&Math.abs(p.lat)<=90&&Math.abs(p.lon)<=180&&p.accuracy!==null&&p.accuracy>=0&&p.accuracy<=45&&agora-p.timestamp<=20000&&p.timestamp<=agora+5000;
}
export function avaliarEtapa(e:EtapaGPS|undefined,p:PosicaoGPS,estado:Evidencia,agora=Date.now()){
 const retorno={estado,concluiu:false};
 if(!e?.inicio_geo||!e.fim_geo||!gpsValido(p,agora)||p.timestamp<=estado.ultimo)return retorno;
 const caminhada=e.modal==="WALK", raio=caminhada?35:65;
 const precisao=p.accuracy!;
 if(distancia(e.inicio_geo,e.fim_geo)<raio*2)return retorno;
 const novo={...estado,ultimo:p.timestamp};
 const inicio=distancia(p,e.inicio_geo),fim=distancia(p,e.fim_geo);
 if(inicio+precisao<=Math.max(raio,75))novo.inicioVisto=true;
 if(novo.inicioVisto&&inicio-precisao>raio)novo.afastou=true;
 if(novo.inicioVisto&&novo.afastou&&fim+precisao<=raio){
   novo.confirmacoes++;
 }else novo.confirmacoes=0;
 return {estado:novo,concluiu:novo.confirmacoes>=2};
}
