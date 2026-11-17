import React, {useState,useEffect} from "react";
import {ActivityIndicator, Pressable, StyleSheet, Text, View} from "react-native";
import {Ionicons} from "@expo/vector-icons";

export type HorarioOnibus = {etapa:number;linha:string|null;sentido:string|null;operadora:string|null;operadora_id:string|null;codigo_linha:string|null;ponto:string|null;ponto_id:string|null;desembarque:string|null;desembarque_id:string|null;partida:string|null;chegada:string|null;partida_programada:string|null;tempo_real:boolean};
type Partida = {partida:string;programada:string|null;tempo_real:boolean;viagem_id:string|null};
type Consulta = {partidas:Partida[];consultado_em:string;aviso:string;dia:string};
const relogio=(s:string)=>new Intl.DateTimeFormat("pt-BR",{timeZone:"America/Sao_Paulo",hour:"2-digit",minute:"2-digit",hourCycle:"h23"}).format(new Date(s));
function dataSP(amanha=false){const d=new Date(Date.now()+(amanha?86400000:0));const p=new Intl.DateTimeFormat("en-CA",{timeZone:"America/Sao_Paulo",year:"numeric",month:"2-digit",day:"2-digit"}).formatToParts(d);return ["year","month","day"].map(k=>p.find(x=>x.type===k)?.value).join("-");}
function hora(s?:string|null){
 if(!s)return "Não informado";
 const d=new Date(s);
 return Number.isNaN(d.getTime())?"Não informado":new Intl.DateTimeFormat("pt-BR",{timeZone:"America/Sao_Paulo",day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit",hourCycle:"h23"}).format(d);
}
function Linha({item,api}:{item:HorarioOnibus;api:string}){
 const [dados,setDados]=useState<Consulta|null>(null);
 const [carregando,setCarregando]=useState(false);
 const [erro,setErro]=useState("");
 const [dia,setDia]=useState(dataSP());
 const [agora,setAgora]=useState(Date.now());
 useEffect(()=>{const t=setInterval(()=>setAgora(Date.now()),15000);return ()=>clearInterval(t);},[]);
 const proxima=dados?.partidas.find(p=>Date.parse(p.partida)>=agora);
 const espera=proxima?Math.max(0,Math.ceil((Date.parse(proxima.partida)-agora)/60000)):null;
 const disponivel=!!(item.ponto_id&&item.codigo_linha&&item.operadora_id&&item.sentido&&item.desembarque_id);
 async function consultar(data=dia){
   if(!disponivel||carregando)return;
   setCarregando(true);setErro("");setDados(null);setDia(data);setAgora(Date.now());
   try{
     const r=await fetch(api+"/horarios/onibus",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ponto_id:item.ponto_id,codigo_linha:item.codigo_linha,operadora_id:item.operadora_id,sentido:item.sentido,desembarque_id:item.desembarque_id,dia:data})});
     const d=await r.json();
     if(!r.ok||!Array.isArray(d.partidas))throw new Error(typeof d.detail==="string"?d.detail:"Horários indisponíveis.");
     setDados(d);
   }catch(e){setErro(e instanceof Error?e.message:"Não foi possível consultar horários.");}
   finally{setCarregando(false);}
 }
 useEffect(()=>{if(disponivel)void consultar(dataSP());},[]);
 return <View style={s.card}>
   <View style={s.row}><View style={s.icon}><Ionicons name="bus-outline" size={23} color="#0071e3"/></View><View style={{flex:1}}><Text style={s.title}>Linha {item.linha||"não informada"}</Text><Text style={s.sub}>Etapa {item.etapa} · {item.operadora||"Operadora não informada"}{item.sentido?" · Sentido "+item.sentido:""}</Text></View></View>
   <View style={s.stop}><Text style={s.label}>EMBARQUE</Text><Text style={s.name}>{item.ponto||"Ponto não informado"}</Text><Text style={s.label}>DESEMBARQUE</Text><Text style={s.name}>{item.desembarque||"Ponto não informado"}</Text></View>
   <Text style={s.label}>HORÁRIO DO TRAJETO CALCULADO</Text>
   <View style={s.times}><View style={{flex:1}}><Text style={s.sub}>Passagem no ponto</Text><Text style={s.time}>{hora(item.partida)}</Text></View><View style={{flex:1}}><Text style={s.sub}>Chegada ao desembarque</Text><Text style={s.time}>{hora(item.chegada)}</Text></View></View>
   <Text style={s.sub}>{item.tempo_real?"Previsão com dados em tempo real do provedor na consulta.":"Horário de referência do itinerário; sem confirmação em tempo real."}</Text>
   {item.tempo_real&&item.partida_programada&&<Text style={s.sub}>Programado: {hora(item.partida_programada)}</Text>}
   <Pressable accessibilityRole="button" disabled={!disponivel||carregando} style={[s.button,(!disponivel||carregando)&&{opacity:.55}]} onPress={()=>consultar()}>{carregando?<ActivityIndicator color="white"/>:<Ionicons name="refresh-outline" size={18} color="#fff"/>}<Text style={s.buttonText}>Atualizar horários</Text></Pressable>
   {!disponivel&&<Text style={s.sub}>O provedor não informou todos os identificadores necessários para consultar a parada.</Text>}
   {!!erro&&<Text style={s.error}>{erro}</Text>}
   <View style={s.dayRow}>{[{label:"Hoje",date:dataSP()},{label:"Amanhã",date:dataSP(true)}].map(d=><Pressable key={d.date} disabled={!disponivel||carregando} onPress={()=>consultar(d.date)} style={[s.day,dia===d.date&&s.dayActive]} accessibilityRole="button" accessibilityState={{selected:dia===d.date}}><Text style={[s.dayText,dia===d.date&&{color:"#fff"}]}>{d.label}</Text></Pressable>)}</View>
   {dados&&<View style={{gap:12}}>
     <View style={s.next}><Text style={s.nextLabel}>PRÓXIMA PASSAGEM NO PONTO</Text>{proxima?<><Text style={s.nextTime}>{relogio(proxima.partida)}</Text><Text style={s.nextText}>{espera===0?"Agora":espera+" min restantes"} · {proxima.tempo_real?"Previsão em tempo real":"Horário programado"}</Text></>:<Text style={s.nextText}>Nenhuma próxima passagem disponível neste dia. Consulte amanhã.</Text>}</View>
     <Text style={s.title}>Horários do dia · {dados.partidas.length} passagens</Text>
     <Text style={s.sub}>Horários anteriores em cinza. Próxima passagem em azul. A previsão considera o ponto, não o tempo necessário para chegar até ele.</Text>
     <View style={s.schedule}>{dados.partidas.map((p,i)=>{const passou=Date.parse(p.partida)<agora;const destaque=p===proxima;return <View key={p.partida+"-"+i} style={[s.slot,passou&&s.past,destaque&&s.highlight]}><Text style={[s.slotTime,passou&&{color:"#64748b"},destaque&&{color:"#fff"}]}>{relogio(p.partida)}</Text><Text style={[s.slotLabel,destaque&&{color:"#fff"}]}>{destaque?"Próximo":passou?"Anterior":p.tempo_real?"Ao vivo":"Programado"}</Text></View>})}</View>
     {!dados.partidas.length&&<Text style={s.sub}>Nenhum horário compatível retornado. Não significa ausência de serviço.</Text>}
     <Text style={s.sub}>Consulta: {hora(dados.consultado_em)} · {dados.aviso}</Text>
   </View>}
 </View>;
}
export default function HorariosOnibus({horarios,temRota,carregando,api,voltar}:{horarios:HorarioOnibus[];temRota:boolean;carregando:boolean;api:string;voltar:()=>void}){
 return <View style={s.page}>
   <Text style={s.eyebrow}>MOBILIDADE URBANA · SÃO PAULO</Text><Text style={s.heading}>Horários dos ônibus</Text><Text style={s.sub}>Acompanhe as passagens nas paradas do trajeto selecionado. Horários no fuso de São Paulo.</Text>
   <Pressable onPress={voltar} accessibilityRole="button" style={s.back}><Ionicons name="arrow-back-outline" size={18} color="#0071e3"/><Text style={s.link}>Voltar ao planejamento</Text></Pressable>
   {carregando?<ActivityIndicator color="#0071e3"/>:!temRota?<View style={s.card}><Text style={s.title}>Planeje um trajeto primeiro</Text><Text style={s.sub}>Os ônibus aparecerão aqui quando houver uma rota calculada.</Text></View>:!horarios.length?<View style={s.card}><Text style={s.title}>Sem horários de ônibus disponíveis</Text><Text style={s.sub}>O trajeto pode não incluir ônibus ou o provedor ainda não informou as etapas. Recalcule o trajeto para atualizar.</Text></View>:horarios.map((item,i)=><Linha key={JSON.stringify(item)+"-"+i} item={item} api={api}/>)}
   <Text style={s.sub}>Fonte: Transitous / MOTIS. Os horários podem mudar. Partidas posteriores não garantem as conexões do itinerário original; recalcule a rota se mudar o embarque.</Text>
 </View>;
}
const s=StyleSheet.create({
 page:{gap:14,paddingVertical:24},eyebrow:{fontSize:11,color:"#0069d2",letterSpacing:1.4,fontWeight:"600"},heading:{fontSize:30,fontWeight:"600",color:"#1d2633"},title:{fontSize:17,fontWeight:"600",color:"#1d2633"},sub:{fontSize:12,color:"#64748b",lineHeight:19},name:{fontSize:14,fontWeight:"600",color:"#1d2633"},label:{fontSize:10,fontWeight:"600",color:"#64748b",letterSpacing:.7},time:{fontSize:18,fontWeight:"600",color:"#0069d2"},card:{padding:18,gap:12,backgroundColor:"#fff",borderRadius:20,borderWidth:1,borderColor:"#d9e6f5"},row:{flexDirection:"row",alignItems:"center",gap:10},icon:{backgroundColor:"#eaf3fc",padding:10,borderRadius:12},stop:{padding:12,gap:6,backgroundColor:"#f3f7fb",borderRadius:12},times:{flexDirection:"row",flexWrap:"wrap",gap:12},button:{backgroundColor:"#0071e3",borderRadius:12,minHeight:44,alignItems:"center",justifyContent:"center",flexDirection:"row",gap:8},buttonText:{color:"#fff",fontWeight:"600",fontSize:13},back:{flexDirection:"row",alignItems:"center",gap:7,alignSelf:"flex-start",paddingVertical:8},link:{color:"#0069d2",fontWeight:"600",fontSize:13},departure:{flexDirection:"row",justifyContent:"space-between",alignItems:"center",gap:8,borderBottomWidth:1,borderBottomColor:"#e4edf5",paddingVertical:10},error:{color:"#a13e20",fontSize:12},dayRow:{flexDirection:"row",gap:8},day:{padding:10,borderRadius:9,backgroundColor:"#eaf3fc"},dayActive:{backgroundColor:"#0071e3"},dayText:{color:"#0069d2",fontWeight:"600",fontSize:13},next:{backgroundColor:"#e8f3ff",borderWidth:1,borderColor:"#b8d9fc",borderRadius:14,padding:18,gap:5},nextLabel:{fontSize:11,color:"#0069d2",fontWeight:"600",letterSpacing:1},nextTime:{fontSize:40,color:"#0069d2",fontWeight:"700"},nextText:{fontSize:14,color:"#234c77"},schedule:{flexDirection:"row",flexWrap:"wrap",gap:8},slot:{minWidth:88,padding:10,borderRadius:10,backgroundColor:"#edf5fc",alignItems:"center"},past:{backgroundColor:"#f1f2f4"},highlight:{backgroundColor:"#0071e3"},slotTime:{fontSize:18,fontWeight:"600",color:"#1d2633"},slotLabel:{fontSize:10,color:"#64748b",marginTop:4}
});
