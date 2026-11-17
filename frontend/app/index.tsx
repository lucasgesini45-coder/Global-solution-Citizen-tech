import React, { useEffect, useState, useRef } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet,
 Text as RNText, TextInput, View, Platform, Linking, useWindowDimensions } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import * as Location from "expo-location";
import MapaPreview from "../components/MapaPreview";
import MetroNetwork from "../components/MetroNetwork";
import HorariosOnibus, {type HorarioOnibus} from "../components/HorariosOnibus";
import {AssistenteViagem, PlanejamentoEconomico, type EtapaViagem, type CustoViagem, type AlternativaEconomica} from "../components/ViagemEconomia";

import {avaliarEtapa,novaEvidencia,gpsValido,type PosicaoGPS} from "../components/gpsViagem";

const API = (process.env.EXPO_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

// Aparência iOS: usa a fonte de sistema (SF Pro em Apple) sem baixar fontes.
// No Windows, usa Segoe UI; no Android/iOS, mantém a fonte nativa.
const fonteInterface = Platform.OS === "web"
  ? "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', Arial, sans-serif"
  : undefined;
function Text(props: React.ComponentProps<typeof RNText>) {
  return <RNText {...props} style={[fonteInterface?{fontFamily:fonteInterface}:null,props.style]} />;
}

type Icon = React.ComponentProps<typeof Ionicons>["name"];
type Modal = "todos"|"ferroviario"|"onibus"|"ape";
type Endereco = {nome:string;lat:number;lon:number;fonte:string};
type Trecho = {modal:string;linha?:string|null;cor_linha?:string|null;paradas?:{nome:string;lat:number;lon:number}[];destino_linha?:string|null;de:string;para:string;tempo_min:number;trajeto:number[][]};
type Resultado = {etapas_viagem?:EtapaViagem[];economia?:CustoViagem;alternativas_economicas?:AlternativaEconomica[];horarios_onibus?:HorarioOnibus[];tipo:string;fonte:string;tempo_min:number;distancia_m:number|null;tarifa_centavos:number|null;seguranca:{status:string};trajeto:number[][];trechos?:Trecho[];aviso:string;modal?:string;caminhada_m?:number|null;caminhada_longa?:boolean;acessibilidade?:{status:string;aviso:string;solicitou_sem_degraus?:boolean}};
type PerguntaAcademica = {numero:number;pergunta:string;categoria:string};
type FonteAgente = {referencia:string;data_verificacao:string;titulo?:string};
type Consulta = {resposta:string;origem_resposta:string;fontes:FonteAgente[];sugestoes:string[];aviso:string|null;rota:Resultado|null};
type RotaDemo = {ordem:number;tempo_total_min:number;espera_min:number;caminhada_m:number;baldeacoes:number;saida:string;chegada:string;custo:{centavos:number|null;confirmado:boolean};seguranca:{status:string};acessibilidade:string;trechos:{tipo:string;modal:string|null;linha:string|null}[]};
type RespostaDemo = {modo:string;origem_dados:string;cenario:string;partida_exemplo:string;aviso:string;resultado:{rotas:RotaDemo[];erro?:{mensagem:string}|null}};


const transportes: {id:Modal;nome:string;icone:Icon}[] = [
 {id:"ferroviario",nome:"Metrô",icone:"train-outline"},
 {id:"onibus",nome:"Ônibus",icone:"bus-outline"},
 {id:"ape",nome:"A pé",icone:"walk-outline"},
];
const sugestoesChat=["Quanto custa a passagem de metrô?","Como emitir cartão comum?","Como pedir gratuidade PCD?","Posso levar bicicleta dobrável no metrô?"];

function Icone({name,color="#5e62bd",size=20}:{name:Icon;color?:string;size?:number}) {
 return <Ionicons name={name} color={color} size={size}/>;
}

function CampoEndereco({titulo,valor,mudar,selecionar,escolhido,placeholder}:{
 titulo:string;valor:string;mudar:(v:string)=>void;selecionar:(v:Endereco)=>void;
 escolhido:Endereco|null;placeholder:string;
}) {
 const [lista,setLista]=useState<Endereco[]>([]);
 const [buscando,setBuscando]=useState(false);
 const [mensagem,setMensagem]=useState("");
 useEffect(()=>{
   if(escolhido || valor.trim().length<4){setLista([]);setMensagem("");setBuscando(false);return;}
   const controller=new AbortController();
   const timer=setTimeout(async()=>{
     setBuscando(true);setMensagem("");
     try{
       const resp=await fetch(API+"/enderecos/sugestoes?q="+encodeURIComponent(valor.trim()),{signal:controller.signal});
       if(!resp.ok){
         const detalhe=await resp.json().catch(()=>null);
         setLista([]);
         setMensagem(resp.status===429?"Muitas pesquisas seguidas. Tente novamente em alguns segundos.":(detalhe?.detail||"Não foi possível consultar os endereços. Confira o backend."));
         return;
       }
       const data=await resp.json();
       setLista(Array.isArray(data.resultados)?data.resultados.filter((p:Endereco)=>Number.isFinite(p.lat)&&Number.isFinite(p.lon)).slice(0,8):[]);
       if(!data.resultados?.length)setMensagem("Nenhum endereço encontrado. Experimente informar rua e bairro ou cidade.");
     }catch(e){if(!controller.signal.aborted){setLista([]);setMensagem("Não foi possível acessar a busca em "+API+". Verifique se a API está iniciada.");}}
     finally{if(!controller.signal.aborted)setBuscando(false);}
   },850);
   return ()=>{clearTimeout(timer);controller.abort();};
 },[valor,escolhido]);
 return <View style={s.autocomplete}>
   <Text style={s.inputLabel}>{titulo} {escolhido && <Icone name="checkmark-circle" color="#3d9a81" size={14}/>}</Text>
   <View style={s.inputWrap}>
     <Icone name="location-outline" size={20} color="#0069d2"/>
     <TextInput accessibilityLabel={titulo} value={valor} onChangeText={mudar}
       placeholder={placeholder} placeholderTextColor="#99a4c0" style={s.textInput}/>
     {buscando && <ActivityIndicator size="small" color="#635fbe"/>}
   </View>
   {!!lista.length && <View style={s.drop} accessibilityLabel={"Sugestões de "+titulo}>
     {lista.map((end,i)=><Pressable key={i} style={s.dropItem} onPress={()=>{selecionar(end);setLista([]);setMensagem("");}} accessibilityRole="button" accessibilityLabel={"Selecionar "+end.nome}>
       <Icone name="location-outline" color="#5b67b2" size={17}/>
       <Text style={s.dropText} numberOfLines={2}>{end.nome}</Text>
     </Pressable>)}
   </View>}
   {!!mensagem && !escolhido && <Text style={s.hint}>{mensagem}</Text>}
 </View>;
}

// Desktop: rolagem própria em cada painel. Mobile: rolagem natural da página.
function PainelRolavel({children,mobile,id}:{children:React.ReactNode;mobile:boolean;id:string}){
 if(mobile)return <View style={v.panelContentMobile}>{children}</View>;
 return <ScrollView nativeID={id} style={v.panelScroll} contentContainerStyle={v.panelContent}
   nestedScrollEnabled showsVerticalScrollIndicator persistentScrollbar
   keyboardShouldPersistTaps="handled">{children}</ScrollView>;
}

export default function Home(){
 const {width,height}=useWindowDimensions();const mobile=width<1180;
 const [aba,setAba]=useState<"planejar"|"metro"|"horarios"|"viagem"|"economia">("planejar");
 const alturaPainel=Math.max(520,Math.min(760,Math.round(height-245)));
 const [alturaMapa,setAlturaMapa]=useState(400);
 const [modal,setModal]=useState<Modal>("todos");
 const [origem,setOrigem]=useState("");const [destino,setDestino]=useState("");
 const [origemGeo,setOrigemGeo]=useState<Endereco|null>(null);const [destinoGeo,setDestinoGeo]=useState<Endereco|null>(null);
 const [localizando,setLocalizando]=useState(false);const [carregando,setCarregando]=useState(false);
 const [erro,setErro]=useState("");const [resultado,setResultado]=useState<Resultado|null>(null);
 const [etapaAtual,setEtapaAtual]=useState(0);
 const [gpsAtivo,setGpsAtivo]=useState(false);
 const [seguirGPS,setSeguirGPS]=useState(true);
 const [posicao,setPosicao]=useState<PosicaoGPS|null>(null);
 const [avisoGPS,setAvisoGPS]=useState("");
 const [relogioGPS,setRelogioGPS]=useState(Date.now());
 const evidencia=useRef(novaEvidencia(0));
 useEffect(()=>{
   if(!gpsAtivo){setPosicao(null);setAvisoGPS("");return;}
   let ativo=true,subscricao:Location.LocationSubscription|undefined;
   setAvisoGPS("Aguardando localização...");
   async function iniciar(){
     try{
       const permissao=await Location.requestForegroundPermissionsAsync();
       if(!ativo)return;
       if(permissao.status!=="granted"){setAvisoGPS("Permissão negada. Use o modo manual ou habilite o GPS nas configurações.");return;}
       const s=await Location.watchPositionAsync({accuracy:Location.Accuracy.High,timeInterval:3000,distanceInterval:5},l=>{
         if(!ativo)return;
         setPosicao({lat:l.coords.latitude,lon:l.coords.longitude,accuracy:l.coords.accuracy,timestamp:l.timestamp});
         setRelogioGPS(Date.now());setAvisoGPS("");
       });
       if(ativo)subscricao=s;else s.remove();
     }catch{if(ativo)setAvisoGPS("GPS indisponível. Confira as permissões e a conexão.");}
   }
   void iniciar();
   const timer=setInterval(()=>setRelogioGPS(Date.now()),3000);
   return ()=>{ativo=false;subscricao?.remove();clearInterval(timer);};
 },[gpsAtivo]);
 const gpsConfiavel=gpsValido(posicao,relogioGPS);
 const statusGPS=!gpsAtivo?"GPS desativado":avisoGPS||(gpsConfiavel?"GPS ativo · acompanhando sua posição":"Aguardando sinal GPS com precisão suficiente");
 function alternarGPS(){if(gpsAtivo){setGpsAtivo(false);}else{setSeguirGPS(true);setGpsAtivo(true);}}
 const [opcaoEconomica,setOpcaoEconomica]=useState<number|null>(null);
 const etapasAtuais:EtapaViagem[]=resultado?.etapas_viagem??(resultado?.trechos||[]).map((t,i)=>({...t,etapa:i+1,paradas:t.paradas?.map(p=>p.nome)}));
 useEffect(()=>{setEtapaAtual(0);setOpcaoEconomica(null);evidencia.current=novaEvidencia(0);},[resultado]);
 useEffect(()=>{
   if(evidencia.current.indice!==etapaAtual)evidencia.current=novaEvidencia(etapaAtual);
 },[etapaAtual]);
 useEffect(()=>{
   if(!gpsAtivo||!gpsConfiavel||!posicao||!resultado||etapaAtual>=etapasAtuais.length)return;
   const r=avaliarEtapa(etapasAtuais[etapaAtual],posicao,evidencia.current,relogioGPS);
   evidencia.current=r.estado;
   if(r.concluiu){evidencia.current=novaEvidencia(etapaAtual+1);setEtapaAtual(i=>i===etapaAtual?i+1:i);}
 },[posicao,gpsAtivo,gpsConfiavel,etapaAtual,resultado,relogioGPS]);
 const controleGPS=<View style={{gap:6,paddingVertical:8}}><View style={{flexDirection:"row",gap:8,flexWrap:"wrap"}}><Pressable onPress={alternarGPS} style={v.detailsToggle} accessibilityRole="button"><Icone name="locate-outline" size={17} color="#0069d2"/><Text style={v.detailsToggleText}>{gpsAtivo?"Desativar GPS":"Ativar GPS em tempo real"}</Text></Pressable>{gpsAtivo&&<Pressable onPress={()=>setSeguirGPS(x=>!x)} style={v.detailsToggle} accessibilityRole="button"><Text style={v.detailsToggleText}>{seguirGPS?"Pausar centralização":"Seguir localização"}</Text></Pressable>}</View><Text style={{fontSize:12,color:gpsConfiavel?"#008e5a":"#64748b"}}>{statusGPS}{posicao?.accuracy!=null?" · precisão ±"+Math.round(posicao.accuracy)+" m":""}</Text></View>;
 function usarAlternativa(o:AlternativaEconomica){
   if(!resultado)return;
   setResultado({...resultado,tempo_min:o.tempo_min,caminhada_m:o.caminhada_m,caminhada_longa:o.caminhada_m!==null&&o.caminhada_m>1500,distancia_m:null,tarifa_centavos:null,trajeto:o.trajeto,trechos:o.trechos,etapas_viagem:o.etapas_viagem,horarios_onibus:o.horarios_onibus,economia:o.custo,modal:o.modal,aviso:"Alternativa do Transitous. Confira horários, acessibilidade e valores nos canais oficiais."});
   setAba("planejar");
 }
 const [chatTexto,setChatTexto]=useState("");const [chat,setChat]=useState<{autor:"pessoa"|"agente";texto:string;fonte?:string;fontes?:FonteAgente[];aviso?:string;sugestoes?:string[]}[]>([]);
 const [chatCarregando,setChatCarregando]=useState(false);
 const [perguntasAcademicas,setPerguntasAcademicas]=useState<PerguntaAcademica[]>([]);
 const [erroPerguntas,setErroPerguntas]=useState("");
 const [filtroAcademico,setFiltroAcademico]=useState<"Todas"|"Consulta"|"Limitação">("Todas");
 async function carregarPerguntas(){
   setErroPerguntas("");
   try{
     const r=await fetch(API+"/agente/perguntas-academicas");
     if(!r.ok)throw new Error();
     const dados=await r.json();
     if(!Array.isArray(dados))throw new Error();
     setPerguntasAcademicas(dados);
   }catch{setErroPerguntas("Não foi possível carregar as perguntas. Confira o backend.");}
 }
 useEffect(()=>{void carregarPerguntas();},[]);
 const [demo,setDemo]=useState<RespostaDemo|null>(null);
 const [demoCarregando,setDemoCarregando]=useState(false);
 const [demoErro,setDemoErro]=useState("");
 const [selecionarNoMapa,setSelecionarNoMapa]=useState<"origem"|"destino"|null>(null);
 const [fotoBase,setFotoBase]=useState(false);
 const [evitarEscadas,setEvitarEscadas]=useState(false);
 const [menosCaminhada,setMenosCaminhada]=useState(false);
 const [mostrarLaboratorio,setMostrarLaboratorio]=useState(false);
 const [mostrarDetalhes,setMostrarDetalhes]=useState(false);

 const pontos=[origemGeo?{...origemGeo,tipo:"origem"}:null,destinoGeo?{...destinoGeo,tipo:"destino"}:null].filter((p):p is Endereco & {tipo:string}=>p!==null);
 const lat=origemGeo?.lat||destinoGeo?.lat||-23.55,lon=origemGeo?.lon||destinoGeo?.lon||-46.63;
 const bbox=[lon-.06,lat-.06,lon+.06,lat+.06].join("%2C");
 const preview="https://www.openstreetmap.org/export/embed.html?bbox="+bbox+"&layer=mapnik";

 const atualizarOrigem=(t:string)=>{setOrigem(t);setOrigemGeo(null);setResultado(null);setErro("");};
 const marcarNoMapa=(lat:number,lon:number)=>{
   const tipo=selecionarNoMapa;
   if(!tipo||!Number.isFinite(lat)||!Number.isFinite(lon))return;
   const ponto:Endereco={nome:"Ponto marcado no mapa ("+lat.toFixed(5)+", "+lon.toFixed(5)+")",lat,lon,fonte:"Positron / coordenadas selecionadas"};
   if(tipo==="origem"){setOrigem(ponto.nome);setOrigemGeo(ponto);}else{setDestino(ponto.nome);setDestinoGeo(ponto);}
   setSelecionarNoMapa(null);setResultado(null);setErro("");
 };
 const atualizarDestino=(t:string)=>{setDestino(t);setDestinoGeo(null);setResultado(null);setErro("");};
 async function obterPosicao(){
   setLocalizando(true);setErro("");
   try{
     const p=await Location.requestForegroundPermissionsAsync();
     if(p.status!=="granted"){setErro("Permissão de localização negada. Informe sua origem.");return;}
     const loc=await Location.getCurrentPositionAsync({accuracy:Location.Accuracy.Balanced});
     const e={nome:"Minha localização",lat:loc.coords.latitude,lon:loc.coords.longitude,fonte:"GPS"};
     setOrigem(e.nome);setOrigemGeo(e);setResultado(null);
   }catch{setErro("Não foi possível acessar sua localização.");}
   finally{setLocalizando(false);}
 }
 async function planejar(){
   setErro("");setResultado(null);
   if(!origemGeo || !destinoGeo){setErro("Selecione um endereço sugerido nos dois campos para calcular a rota.");return;}
   setCarregando(true);
   try{
     const r=await fetch(API+"/rotas/reais",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({
       origem:{lat:origemGeo.lat,lon:origemGeo.lon},destino:{lat:destinoGeo.lat,lon:destinoGeo.lon},modal,
       evitar_escadas:evitarEscadas,priorizar_menos_caminhada:menosCaminhada,
     })});
     const data=await r.json().catch(()=>({}));
     if(!r.ok)throw new Error(data.detail||"Serviço de rotas indisponível.");
     setResultado(data);
   }catch(e){setErro(e instanceof Error?e.message:"Não foi possível calcular a rota.");}
   finally{setCarregando(false);}
 }
 async function executarDemo(){
   if(demoCarregando)return;
   setDemoCarregando(true);setDemoErro("");setDemo(null);
   try{
     const resposta=await fetch(API+"/rotas/exemplo");
     const dados=await resposta.json().catch(()=>null) as (Partial<RespostaDemo> & {detail?:string}) | null;
     if(!resposta.ok)throw new Error("Erro HTTP "+resposta.status+": "+(dados?.detail||"verifique o terminal do backend."));
     if(!dados||dados.modo!=="demonstracao"||!dados.resultado||!Array.isArray(dados.resultado.rotas))
       throw new Error("O backend respondeu, mas o formato da simulação está incorreto.");
     if(dados.resultado.erro)throw new Error(dados.resultado.erro.mensagem);
     setDemo(dados as RespostaDemo);
   }catch(e){
     const mensagem=e instanceof Error?e.message:"Erro desconhecido";
     setDemoErro(/failed to fetch|network request failed|networkerror|load failed/i.test(mensagem)
       ?"Não foi possível conectar à API em "+API+". Confira se o backend Python está rodando e se /health e /rotas/exemplo abrem no navegador."
       :mensagem);
   }
   finally{setDemoCarregando(false);}
 }
 async function perguntar(pergunta=chatTexto){
   const texto=pergunta.trim();
   if(chatCarregando)return;
   if(!texto){setChat(c=>[...c,{autor:"agente",texto:"Digite uma pergunta válida sobre mobilidade urbana."}]);return;}
   setChatTexto("");
   setChat(c=>[...c,{autor:"pessoa",texto}]);
   setChatCarregando(true);
   try{
     const r=await fetch(API+"/agente/conversar",{
       method:"POST",
       headers:{"Content-Type":"application/json"},
       body:JSON.stringify({
         pergunta:texto,
         origem:origemGeo?{lat:origemGeo.lat,lon:origemGeo.lon}:null,
         destino:destinoGeo?{lat:destinoGeo.lat,lon:destinoGeo.lon}:null,
         modal,
         priorizar_menos_caminhada:menosCaminhada,
         evitar_escadas:evitarEscadas,
       }),
     });
     const data=(await r.json().catch(()=>({}))) as Consulta & {detail?:string};
     if(!r.ok){
       const detail=typeof data.detail==="string"?data.detail:"Não foi possível acessar o agente.";
       throw new Error(detail);
     }
     if(data.rota && Array.isArray(data.rota.trajeto) && Array.isArray(data.rota.trechos)){
       setResultado(data.rota);
       setErro("");
     }
     const fontes=(data.fontes||[]).map(f=>f.referencia+(f.data_verificacao?" · "+f.data_verificacao:"")).join(" · ");
     const academic=data.origem_resposta==="classificador_academico"?"Base acadêmica · resposta não verificada oficialmente":undefined;
     setChat(c=>[...c,{
       autor:"agente",
       texto:data.resposta,
       fonte:academic||(!data.fontes?.length?fontes:undefined),
       fontes:data.fontes||[],
       aviso:data.aviso||undefined,
       sugestoes:Array.isArray(data.sugestoes)?data.sugestoes.slice(0,3):[],
     }]);
   }catch(e){
     setChat(c=>[...c,{autor:"agente",texto:e instanceof Error?e.message:"Não foi possível consultar o agente."}]);
   }finally{setChatCarregando(false);}
 }

 return <ScrollView style={v.bg} contentContainerStyle={v.page}>
   <View style={[v.nav,mobile&&v.navMobile]}>
     <Text style={[v.navBrand,mobile&&v.navBrandMobile]}>Citizen Tech <Text style={v.navBrandAccent}>Mobilidade Urbana</Text></Text>
     <View style={[v.navTabs,mobile&&v.navTabsMobile]}>
       <Pressable onPress={()=>setAba("planejar")} style={[v.navTab,aba==="planejar"&&v.navActive]} accessibilityRole="tab" accessibilityState={{selected:aba==="planejar"}}><Icone name="navigate-outline" size={17} color={aba==="planejar"?"#0069d2":"#64748b"}/><Text style={[v.navTabText,aba==="planejar"&&v.navActiveText]}>Planejar trajeto</Text></Pressable>
       <Pressable onPress={()=>setAba("metro")} style={[v.navTab,aba==="metro"&&v.navActive]} accessibilityRole="tab" accessibilityState={{selected:aba==="metro"}}><Icone name="train-outline" size={17} color={aba==="metro"?"#0069d2":"#64748b"}/><Text style={[v.navTabText,aba==="metro"&&v.navActiveText]}>Mapa do metrô</Text></Pressable>
       <Pressable onPress={()=>setAba("horarios")} style={[v.navTab,aba==="horarios"&&v.navActive]} accessibilityRole="tab" accessibilityState={{selected:aba==="horarios"}}><Icone name="time-outline" size={17} color={aba==="horarios"?"#0069d2":"#64748b"}/><Text style={[v.navTabText,aba==="horarios"&&v.navActiveText]}>Horários dos ônibus</Text></Pressable>
       <Pressable onPress={()=>setAba("viagem")} style={[v.navTab,aba==="viagem"&&v.navActive]} accessibilityRole="tab" accessibilityState={{selected:aba==="viagem"}}><Icone name="navigate-outline" size={17} color={aba==="viagem"?"#0069d2":"#64748b"}/><Text style={[v.navTabText,aba==="viagem"&&v.navActiveText]}>Assistente de viagem</Text></Pressable>
       <Pressable onPress={()=>setAba("economia")} style={[v.navTab,aba==="economia"&&v.navActive]} accessibilityRole="tab" accessibilityState={{selected:aba==="economia"}}><Icone name="wallet-outline" size={17} color={aba==="economia"?"#0069d2":"#64748b"}/><Text style={[v.navTabText,aba==="economia"&&v.navActiveText]}>Planejamento econômico</Text></Pressable>
     </View>
     <Text style={v.navMeta}>Global Solution · 2026</Text>
   </View>

   <View style={[v.container,mobile&&v.containerMobile]}>
     {aba==="metro"?<MetroNetwork mobile={mobile}/>:aba==="horarios"?<HorariosOnibus api={API} horarios={resultado?.horarios_onibus||[]} temRota={!!resultado} carregando={carregando} voltar={()=>setAba("planejar")}/>:aba==="viagem"?<AssistenteViagem etapas={etapasAtuais} indice={etapaAtual} setIndice={setEtapaAtual} voltar={()=>setAba("planejar")} horarios={()=>setAba("horarios")} recalcular={()=>setAba("planejar")} temRota={!!resultado} carregando={carregando} gpsAtivo={gpsAtivo} statusGPS={statusGPS} mapa={<View>{controleGPS}<MapaPreview url={preview} pontos={pontos} trajeto={resultado?.trajeto} trechos={resultado?.trechos} height={mobile?320:420} posicao={gpsConfiavel?posicao:null} seguir={gpsAtivo&&seguirGPS}/></View>}/>:aba==="economia"?<PlanejamentoEconomico opcoes={resultado?.alternativas_economicas??(resultado?.modal==="ape"&&resultado.tarifa_centavos===0?[{id:1,tempo_min:resultado.tempo_min,caminhada_m:resultado.distancia_m,etapas_viagem:etapasAtuais,horarios_onibus:[],trajeto:resultado.trajeto,trechos:resultado.trechos||[],modal:"ape",custo:{centavos:0,status:"estimativa",detalhes:[],pendencias:[],fontes:[],data_referencia:"2026-11-17",aviso:"Caminhada sem tarifa de transporte."}}]:[])} selecionada={resultado?.alternativas_economicas?.find(o=>o.etapas_viagem===resultado.etapas_viagem||o.trajeto===resultado.trajeto)?.id??opcaoEconomica} selecionar={usarAlternativa} voltar={()=>setAba("planejar")} temRota={!!resultado}/>:<>
     <View style={[v.intro,mobile&&v.introMobile]}>
       <Text style={v.eyebrow}>MENOS COMPLICAÇÃO. MAIS CIDADE.</Text>
       <Text style={[v.heading,mobile&&v.headingMobile]}>Seu próximo destino começa aqui.</Text>
       <Text style={v.subtitle}>Combine metrô, ônibus e caminhada. Encontre o melhor caminho para você.</Text>
       {!mobile&&<View style={v.cityBadge}><Icone name="location-outline" size={17} color="#0069d2"/><Text style={v.cityText}>São Paulo, SP</Text></View>}
     </View>

     <View style={[v.main,mobile?v.mainMobile:{height:alturaPainel}]}>
       <View style={[v.sidebar,mobile&&v.sidebarMobile]}>
         <View style={[v.panelHeader,v.searchHeader]}>
           <Text style={v.searchTitle}>Para onde vamos?</Text>
           <Icone name="navigate-outline" size={18} color="#667c92"/>
         </View>
         <PainelRolavel mobile={mobile} id="citizen-search-scroll">
           <View style={v.modeBar}>
             <Pressable onPress={()=>{setModal("todos");setResultado(null);setErro("");}} style={[v.modeItem,modal==="todos"&&v.modeActive]} accessibilityRole="button" accessibilityState={{selected:modal==="todos"}}><Text style={[v.modeText,modal==="todos"&&v.modeTextActive]}>Todos</Text></Pressable>
             {transportes.map(t=><Pressable key={t.id} onPress={()=>{setModal(t.id);setResultado(null);setErro("");}} style={[v.modeItem,modal===t.id&&v.modeActive]} accessibilityRole="button" accessibilityState={{selected:modal===t.id}}>
               <Icone name={t.icone} size={15} color={modal===t.id?"#0069d2":"#667c92"}/><Text style={[v.modeText,modal===t.id&&v.modeTextActive]}>{t.id==="ferroviario"?"Metrô":t.nome}</Text>
             </Pressable>)}
           </View>
           <View style={v.addresses}>
             <CampoEndereco titulo="ORIGEM" valor={origem} escolhido={origemGeo} mudar={atualizarOrigem} selecionar={e=>{setOrigem(e.nome);setOrigemGeo(e);setResultado(null);}} placeholder="Informe seu ponto de partida"/>
             <View style={v.middleActions}>
               <Pressable onPress={obterPosicao} style={v.smallAction} accessibilityLabel="Usar minha localização">{localizando?<ActivityIndicator size="small" color="#0069d2"/>:<Icone name="locate-outline" color="#0069d2" size={17}/>}</Pressable>
               <Pressable onPress={()=>{setOrigem(destino);setDestino(origem);setOrigemGeo(destinoGeo);setDestinoGeo(origemGeo);setResultado(null);setErro("");}} style={v.smallAction} accessibilityLabel="Inverter origem e destino"><Icone name="swap-vertical-outline" color="#0069d2" size={17}/></Pressable>
             </View>
             <CampoEndereco titulo="DESTINO" valor={destino} escolhido={destinoGeo} mudar={atualizarDestino} selecionar={e=>{setDestino(e.nome);setDestinoGeo(e);setResultado(null);}} placeholder="Para onde você quer ir?"/>
             <View style={{flexDirection:"row",gap:8,flexWrap:"wrap",marginTop:8}}>
               <Pressable onPress={()=>setSelecionarNoMapa(t=>t==="origem"?null:"origem")} accessibilityRole="button" style={{backgroundColor:selecionarNoMapa==="origem"?"#d5eaff":"#f0f5fa",borderRadius:12,padding:10,flexGrow:1}}>
                 <Text style={{color:"#0069d2",fontSize:11,fontWeight:"600"}}>{selecionarNoMapa==="origem"?"Cancelar origem":"Marcar origem no mapa"}</Text>
               </Pressable>
               <Pressable onPress={()=>setSelecionarNoMapa(t=>t==="destino"?null:"destino")} accessibilityRole="button" style={{backgroundColor:selecionarNoMapa==="destino"?"#d5eaff":"#f0f5fa",borderRadius:12,padding:10,flexGrow:1}}>
                 <Text style={{color:"#0069d2",fontSize:11,fontWeight:"600"}}>{selecionarNoMapa==="destino"?"Cancelar destino":"Marcar destino no mapa"}</Text>
               </Pressable>
             </View>
           </View>
           <View style={{marginTop:15,gap:9}}>
             <Text style={{fontSize:12,fontWeight:"600",color:"#445b74"}}>Preferências de mobilidade</Text>
             <Pressable onPress={()=>setMenosCaminhada(x=>!x)} accessibilityRole="checkbox" accessibilityState={{checked:menosCaminhada}} style={{flexDirection:"row",alignItems:"center",gap:9,minHeight:35}}>
               <Icone name={menosCaminhada?"checkbox":"square-outline"} size={20} color="#0069d2"/>
               <Text style={{color:"#425a73",fontSize:12}}>Priorizar menos caminhada</Text>
             </Pressable>
             <Pressable onPress={()=>setEvitarEscadas(x=>!x)} accessibilityRole="checkbox" accessibilityState={{checked:evitarEscadas}} style={{flexDirection:"row",alignItems:"center",gap:9,minHeight:35}}>
               <Icone name={evitarEscadas?"checkbox":"square-outline"} size={20} color="#0069d2"/>
               <Text style={{color:"#425a73",fontSize:12}}>Preciso de percurso sem escadas</Text>
             </Pressable>
             {evitarEscadas&&<Text style={{color:"#855f2f",fontSize:11,lineHeight:16}}>Ainda não há confirmação de rampas ou elevadores nesta rota. A preferência não garante acessibilidade.</Text>}
           </View>
           {!!erro&&<View style={v.warning}><Icone name="information-circle-outline" size={17} color="#94602c"/><Text style={v.warningText}>{erro}</Text></View>}
         </PainelRolavel>
         <View style={v.searchFooter}>
           <Pressable onPress={planejar} disabled={carregando} style={v.searchButton} accessibilityRole="button">
             {carregando?<ActivityIndicator color="#fff" size="small"/>:<Icone name="navigate-outline" size={18} color="#fff"/>}
             <Text style={v.searchButtonText}>{carregando?"Calculando...":"Encontrar trajeto"}</Text>
             <Icone name="arrow-forward-outline" size={18} color="#fff"/>
           </Pressable>
         </View>
       </View>

       <View style={[v.mapCard,mobile&&v.mapCardMobile]}>
         <View style={[v.panelHeader,v.mapHeader]}><Text style={v.mapTitle}>Mapa do trajeto</Text><View style={v.mapBadge}><Icone name="map-outline" size={15} color="#0069d2"/><Text style={v.mapBadgeText}>Mapa interativo</Text></View></View>
         <View style={mobile?v.mapViewportMobile:v.mapViewport} onLayout={e=>{
           if(!mobile){
             const h=Math.max(1,Math.floor(e.nativeEvent.layout.height));
             setAlturaMapa(prev=>prev===h?prev:h);
           }
         }}>
           <MapaPreview url={preview} pontos={pontos} trajeto={resultado?.trajeto} trechos={resultado?.trechos} height={mobile?390:alturaMapa} pickMode={selecionarNoMapa} onMapPick={marcarNoMapa} posicao={gpsConfiavel?posicao:null} seguir={gpsAtivo&&seguirGPS&&!selecionarNoMapa}/>
         </View>
         {controleGPS}
         <View style={v.mapBottom}>
           <Icone name="information-circle-outline" color="#63778c" size={17}/>
           <Text style={v.mapBottomText}>{resultado?"Trajeto calculado a partir dos dados de "+resultado.fonte+". Consulte as etapas e confira horários antes de sair.":"Selecione origem e destino e clique em Encontrar trajeto. O percurso só aparece quando o provedor retornar a geometria real."}</Text>
         </View>
       </View>

       <View style={[v.routesPanel,mobile&&v.routesPanelMobile]}>
         <View style={[v.panelHeader,v.resultsHeader]}><Text style={v.resultsTitle}>Trajetos sugeridos</Text><Icone name="options-outline" size={20} color="#667c92"/></View>
         <PainelRolavel mobile={mobile} id="citizen-routes-scroll">
         <View style={v.departure}><Icone name="time-outline" size={15} color="#667c92"/><Text style={v.departureText}>Rota calculada</Text><Text style={v.departureCount}>{resultado?"1 itinerário":"Aguardando busca"}</Text></View>
         {resultado?<View style={v.recommended}>
            <Text style={v.recommendedBadge}>{"TRAJETO DISPONÍVEL · "+(resultado.modal==="onibus"?"ÔNIBUS":resultado.modal==="ferroviario"?"METRÔ / TREM":resultado.modal==="todos"?"TRANSPORTE PÚBLICO":"A PÉ")}</Text>
            <View style={v.recommendedTop}><Text style={v.duration}>{resultado.tempo_min} min</Text><Text style={v.fare}>{resultado.tarifa_centavos===null?"Tarifa não informada":resultado.tarifa_centavos===0?"Gratuito":"R$ "+(resultado.tarifa_centavos/100).toFixed(2).replace(".",",")}</Text></View>
            <Text style={v.routeSequenceText}>Fonte: Transitous / OpenStreetMap · Horários estimados</Text>
            <Pressable onPress={()=>setAba("viagem")} style={v.detailsToggle} accessibilityRole="button"><Text style={v.detailsToggleText}>Iniciar acompanhamento da viagem</Text><Icone name="navigate-outline" size={17} color="#0069d2"/></Pressable>
            <Pressable onPress={()=>setAba("economia")} style={v.detailsToggle} accessibilityRole="button"><Text style={v.detailsToggleText}>Comparar opções e custos</Text><Icone name="wallet-outline" size={17} color="#0069d2"/></Pressable>
            {!!resultado.horarios_onibus?.length&&<Pressable onPress={()=>setAba("horarios")} style={v.detailsToggle} accessibilityRole="button"><Text style={v.detailsToggleText}>Ver horários dos ônibus</Text><Icone name="time-outline" size={17} color="#0069d2"/></Pressable>}
            <View style={v.itineraryHeader}>
              <Text style={v.itineraryHeading}>Etapas da viagem</Text>
              <Text style={v.itineraryCount}>{(resultado.trechos||[]).length} etapas</Text>
            </View>
            {(resultado.trechos||[]).map((t,i)=>{
              const walk=t.modal==="WALK";
              const bus=t.modal==="BUS";
              const rail=!walk&&!bus;
              const cor=walk?"#5F6D7E":bus?"#0071e3":t.cor_linha||"#7155c8";
              const nome=walk?"A pé":bus?"Ônibus":t.modal==="SUBWAY"||t.modal==="METRO"?"Metrô":"Trem";
              return <View key={i} style={{marginTop:12,paddingLeft:12,borderLeftWidth:5,borderLeftColor:cor,paddingVertical:5}}>
                <View style={{flexDirection:"row",alignItems:"center",gap:7,flexWrap:"wrap"}}>
                  <View style={{backgroundColor:cor,borderRadius:6,paddingVertical:4,paddingHorizontal:7}}>
                    <Text style={{color:"#fff",fontWeight:"700",fontSize:11}}>{nome}</Text>
                  </View>
                  <Text style={{color:"#1d2633",fontWeight:"700",fontSize:13,flexShrink:1}}>
                    {walk?"Caminhar":t.linha|| (bus?"Linha de ônibus não informada":"Linha ferroviária não informada")}
                  </Text>
                  <Text style={{color:"#60768f",fontSize:11}}>{t.tempo_min} min</Text>
                </View>
                <Text numberOfLines={mostrarDetalhes?undefined:3} style={{color:"#526a82",fontSize:12,marginTop:6,lineHeight:18}}>
                  {walk?"Caminhe de "+t.de+" até "+t.para:bus?"Pegue o ônibus em "+t.de+" e desça em "+t.para:"Embarque em "+t.de+" e desça em "+t.para}
                </Text>
                {!!t.destino_linha&&<Text numberOfLines={2} style={{color:"#60768f",fontSize:11,marginTop:4}}>Sentido {t.destino_linha}</Text>}
                {rail&&t.paradas&&t.paradas.length>2&&mostrarDetalhes&&<Text style={{color:"#60768f",fontSize:11,marginTop:4}}>Estações: {t.paradas.map(p=>p.nome).join(" · ")}</Text>}
              </View>;
            })}
            <Pressable onPress={()=>setMostrarDetalhes(x=>!x)} style={v.detailsToggle} accessibilityRole="button">
              <Text style={v.detailsToggleText}>{mostrarDetalhes?"Ocultar estações intermediárias":"Ver estações intermediárias"}</Text>
              <Icone name={mostrarDetalhes?"chevron-up":"chevron-down"} color="#0069d2" size={15}/>
            </Pressable>
            {resultado.caminhada_m!==null&&resultado.caminhada_m!==undefined&&resultado.modal!=="ape"&&<View style={{marginTop:9,padding:10,backgroundColor:resultado.caminhada_longa?"#FFF2DE":"#EDF5FC",borderRadius:10}}>
              <Text style={{color:resultado.caminhada_longa?"#87521A":"#234C77",fontWeight:"600",fontSize:12}}>
                {"Caminhada total: "+(resultado.caminhada_m>=1000?(resultado.caminhada_m/1000).toFixed(1).replace(".",",")+" km":resultado.caminhada_m+" m")}
                {resultado.caminhada_longa?" · Atenção: trecho longo a pé":""}
              </Text>
            </View>}
            {resultado.acessibilidade&&<View style={{marginTop:12,padding:10,backgroundColor:"#FFF7E8",borderRadius:9}}>
              <Text style={{fontSize:11,color:"#825c24",lineHeight:17}}>Acessibilidade não verificada: {resultado.acessibilidade.aviso}</Text>
            </View>}
            <Text style={v.routeDisclaimer}>{resultado.caminhada_longa?"Atenção: avalie uma alternativa com menos caminhada. ":""}Os horários e tarifas podem mudar. Consulte o operador antes de viajar.</Text>
          </View>:<View style={v.emptyResults}><Icone name="git-compare-outline" size={27} color="#8ba2bd"/><Text style={v.emptyResultsTitle}>Seu trajeto aparecerá aqui</Text><Text style={v.emptyResultsCopy}>Selecione endereços sugeridos e um modo de transporte para consultar as opções disponíveis. As rotas são consultadas em serviços externos e podem não estar disponíveis em alguns horários e locais.</Text></View>}
         </PainelRolavel>
       </View>
     </View>

     <View style={v.labSection}>
       <Pressable onPress={()=>setMostrarLaboratorio(x=>!x)} accessibilityRole="button" style={v.labToggle}>
         <View style={{flexDirection:"row",alignItems:"center",gap:9}}><Icone name="flask-outline" color="#56739a" size={18}/><Text style={v.labToggleText}>Laboratório acadêmico de rotas e tarifas</Text></View>
         <Icone name={mostrarLaboratorio?"chevron-up-outline":"chevron-down-outline"} color="#56739a" size={18}/>
       </Pressable>
       {mostrarLaboratorio&&<View style={v.demoPanel}>
           <View style={v.demoHead}><Icone name="flask-outline" color="#0069d2" size={21}/><Text style={v.demoTitle}>Laboratório de rotas e tarifas</Text></View>
           <Text style={v.demoDescription}>Teste o algoritmo do grupo com uma rede fictícia. Os horários, trajetos e preços desta simulação não representam o transporte real.</Text>
           <Pressable style={v.demoButton} onPress={executarDemo} disabled={demoCarregando} accessibilityRole="button">
             {demoCarregando?<ActivityIndicator color="#fff" size="small"/>:<Icone name="play-outline" color="#fff" size={17}/>}
             <Text style={v.demoButtonText}>{demoCarregando?"Executando...":"Executar simulação"}</Text>
           </Pressable>
           {!!demoErro&&<Text style={v.demoError}>{demoErro}</Text>}
           {demo&&<View style={v.demoResults}>
             <Text style={v.demoLabel}>RESULTADOS SIMULADOS · NÃO OFICIAIS</Text>
             <Text style={v.demoDetail}>Cenário acadêmico: 09/11/2026, 08:00 · {demo.resultado.rotas.length} alternativas</Text>
             {demo.resultado.rotas.map((rota,i)=><View style={v.demoRoute} key={i}>
               <View style={v.demoRouteHeader}><Text style={v.demoRouteTitle}>Alternativa {rota.ordem||i+1}</Text><Text style={v.demoMinutes}>{rota.tempo_total_min} min</Text></View>
               <Text style={v.demoDetail}>{rota.saida} – {rota.chegada} · {rota.baldeacoes} baldeação(ões)</Text>
               <Text style={v.demoCost}>{rota.custo.confirmado&&rota.custo.centavos!==null?"Tarifa simulada: R$ "+(rota.custo.centavos/100).toFixed(2).replace(".",","):"Tarifa não confirmada"}</Text>
               <Text style={v.demoDetail}>{rota.trechos.filter(t=>t.tipo==="transporte").map(t=>t.linha||t.modal||"Transporte").join(" · ")||"Somente caminhada"}</Text>
             </View>)}
             {!!demo.aviso&&<Text style={v.demoDetail}>{demo.aviso}</Text>}
           </View>}
         </View>}
     </View>

     <View style={[v.assistantArea,mobile&&v.assistantAreaMobile]}>
     <View style={v.assistant}>
       <View style={v.assistantHeader}>
         <View style={v.assistantHeaderLeft}><Icone name="chatbubble-ellipses-outline" color="#0069d2" size={23}/><View style={{flex:1}}><Text style={v.assistantTitle}>Pergunte ao agente de IA</Text><Text style={v.assistantSubtitle}>Perguntas livres sobre transporte, benefícios, tarifas e acessibilidade, com fontes</Text></View></View>
         <Text style={v.assistantTag}>ASSISTENTE CIDADÃO</Text>
       </View>
       <View style={v.suggestions}>{sugestoesChat.map(t=><Pressable key={t} style={v.suggestion} onPress={()=>perguntar(t)}><Text style={v.suggestionText}>{t}</Text></Pressable>)}</View>
       <ScrollView style={v.chatHistory} nestedScrollEnabled><View style={{gap:10}}>{chat.length===0?<Text style={v.chatEmpty}>Pergunte sobre mobilidade ou peça um trajeto. Para calcular uma viagem, selecione origem e destino no planejador.</Text>:chat.map((m,i)=><View key={i} style={[v.chatBubble,m.autor==="pessoa"?v.chatBubbleUser:v.chatBubbleAi]}><Text style={[v.chatBubbleText,m.autor==="pessoa"&&{color:"#fff"}]}>{m.texto}</Text>{!!m.fonte&&<Text style={v.chatSource}>{m.fonte}</Text>}{m.fontes?.map((f,j)=><Pressable key={j} disabled={!f.referencia.startsWith("https://")} onPress={()=>{void Linking.openURL(f.referencia).catch(()=>{});}} accessibilityRole="link"><Text style={[v.chatSource,{color:"#0069d2"}]}>{f.titulo||f.referencia}{f.data_verificacao?" · "+f.data_verificacao:""}</Text></Pressable>)}{!!m.aviso&&<Text style={v.chatSource}>{m.aviso}</Text>}{!!m.sugestoes?.length&&<View style={{flexDirection:"row",gap:6,flexWrap:"wrap",marginTop:8}}>{m.sugestoes.map((s,j)=><Pressable key={j} onPress={()=>perguntar(s)} style={v.suggestion}><Text style={v.suggestionText}>{s}</Text></Pressable>)}</View>}</View>)}</View></ScrollView>
       <View style={v.chatInput}><TextInput accessibilityLabel="Pergunta para o agente de IA" value={chatTexto} onChangeText={setChatTexto} maxLength={300} placeholder="Escreva sua pergunta..." placeholderTextColor="#9baec2" onSubmitEditing={()=>perguntar()} returnKeyType="send" style={v.chatField}/><Pressable style={v.chatSend} onPress={()=>perguntar()} accessibilityLabel="Enviar pergunta">{chatCarregando?<ActivityIndicator color="#fff"/>:<Icone name="send" size={18} color="#fff"/>}</Pressable></View>
       <Text style={v.assistantFootnote}>Consulta a resumos locais de fontes institucionais. Não responde assuntos externos ao projeto. Confirme informações atualizadas nos links oficiais.</Text>
     </View>
     <View style={[v.academicPanel,mobile&&v.academicMobile]}>
       <View style={v.academicHeader}><Icone name="school-outline" color="#0069d2" size={22}/><View style={{flex:1}}><Text style={v.assistantTitle}>Perguntas da avaliação FIAP</Text><Text style={v.assistantSubtitle}>Cenários elaborados pela equipe conforme o enunciado · {perguntasAcademicas.length} casos</Text></View></View>
       <View style={v.academicFilters}>{(["Todas","Consulta","Limitação"] as const).map(t=><Pressable key={t} style={[v.academicFilter,filtroAcademico===t&&v.navActive]} accessibilityRole="button" accessibilityState={{selected:filtroAcademico===t}} onPress={()=>setFiltroAcademico(t)}><Text style={v.suggestionText}>{t}</Text></Pressable>)}</View>
       <ScrollView style={v.academicScroll} nestedScrollEnabled persistentScrollbar showsVerticalScrollIndicator keyboardShouldPersistTaps="handled">
         {perguntasAcademicas.filter(p=>filtroAcademico==="Todas"||p.categoria===filtroAcademico).map(p=><Pressable key={p.numero} disabled={chatCarregando} style={v.academicQuestion} onPress={()=>perguntar(p.pergunta)} accessibilityRole="button">
           <View style={v.academicNumber}><Text style={v.suggestionText}>{String(p.numero).padStart(2,"0")}</Text></View>
           <View style={{flex:1}}><Text style={v.chatBubbleText}>{p.pergunta||"Entrada vazia (teste de validação)"}</Text><Text style={v.assistantSubtitle}>{p.categoria}</Text></View><Icone name="arrow-forward-outline" size={15} color="#0069d2"/>
         </Pressable>)}
         {!!erroPerguntas&&<Pressable onPress={carregarPerguntas}><Text style={v.chatSource}>{erroPerguntas} Toque para tentar novamente.</Text></Pressable>}
       </ScrollView>
       <Text style={v.assistantFootnote}>Clique para testar no chat. Os indicadores A/B documentados são do núcleo acadêmico, avaliado separadamente.</Text>
     </View>
     </View>

     </>}
     <Text style={v.footer}>Citizen Tech Mobilidade Urbana · FIAP Global Solution 2026 · Indicadores de segurança não verificados; dados de viagens provenientes do Transitous quando disponíveis.</Text>
   </View>
 </ScrollView>;
}

const s=StyleSheet.create({
 autocomplete:{position:"relative",zIndex:10},
 inputLabel:{fontSize:10,fontWeight:"700",color:"#586c80",marginBottom:6,letterSpacing:.8},
 inputWrap:{minHeight:58,borderRadius:14,backgroundColor:"#f0f5fa",flexDirection:"row",alignItems:"center",paddingHorizontal:14,gap:9},
 textInput:{flex:1,fontFamily:fonteInterface,fontSize:13,fontWeight:"500",color:"#1d2633",paddingVertical:10,minWidth:0},
 drop:{backgroundColor:"#fff",borderWidth:1,borderColor:"#c7ddeb",borderRadius:12,marginTop:4,overflow:"hidden",zIndex:20,elevation:5},
 dropItem:{padding:11,flexDirection:"row",gap:8,borderBottomWidth:1,borderBottomColor:"#f0f5fa",alignItems:"center"},
 dropText:{color:"#1d2633",fontSize:13,flex:1},
 hint:{fontSize:11,color:"#71859b",marginTop:5}
});

const v=StyleSheet.create({
 bg:{flex:1,backgroundColor:"#dfefff"},
 page:{minHeight:"100%"},
 nav:{backgroundColor:"rgba(247,251,255,0.90)",minHeight:88,paddingHorizontal:48,paddingVertical:20,borderBottomWidth:1,borderBottomColor:"#bfd6ec",flexDirection:"row",alignItems:"center",gap:30,flexWrap:"wrap"},
 navMobile:{minHeight:68,paddingHorizontal:16,paddingVertical:15,gap:10},navBrand:{fontSize:24,fontWeight:"600",letterSpacing:-1.1,color:"#1d2633"},navBrandMobile:{fontSize:19},navBrandAccent:{fontWeight:"500",color:"#0069d2"},
 navTabs:{flexDirection:"row",alignItems:"center",gap:8,flexWrap:"wrap"},navTabsMobile:{width:"100%"},navTab:{flexDirection:"row",alignItems:"center",gap:7,paddingHorizontal:14,paddingVertical:11,borderRadius:14},navTabText:{color:"#64748b",fontSize:13,fontWeight:"500"},navActive:{backgroundColor:"#dcebfa"},navActiveText:{color:"#0069d2",fontSize:14,fontWeight:"600"},navMeta:{fontSize:11,color:"#62758a",marginLeft:"auto"},
 container:{maxWidth:1440,width:"100%",alignSelf:"center",paddingHorizontal:48,paddingBottom:28},
 containerMobile:{paddingHorizontal:16},intro:{minHeight:140,paddingTop:22,justifyContent:"center",position:"relative",paddingBottom:18},introMobile:{paddingTop:24,minHeight:0},
 eyebrow:{color:"#0069d2",fontSize:11,fontWeight:"700",letterSpacing:1.7,marginBottom:12},
 heading:{color:"#1d2633",fontWeight:"700",fontSize:32,letterSpacing:-0.8,lineHeight:43},headingMobile:{fontSize:29,lineHeight:38},
 subtitle:{color:"#586c80",fontSize:15,marginTop:7,lineHeight:22},
 cityBadge:{position:"absolute",right:0,top:70,flexDirection:"row",alignItems:"center",gap:8,backgroundColor:"rgba(255,255,255,.7)",borderRadius:24,paddingHorizontal:16,paddingVertical:13},cityText:{color:"#1d2633",fontSize:13,fontWeight:"500"},
 main:{flexDirection:"row",alignItems:"stretch",gap:14},mainMobile:{flexDirection:"column",alignItems:"stretch"},
 sidebar:{width:272,maxWidth:"100%",flexShrink:0,minHeight:0,backgroundColor:"#fff",borderRadius:20,borderWidth:1,borderColor:"#d9e6f5",padding:12},sidebarMobile:{width:"100%"},
 routesPanel:{width:324,maxWidth:"100%",flexShrink:0,minHeight:0,backgroundColor:"#fff",borderRadius:20,padding:12,borderWidth:1,borderColor:"#d9e6f5"},routesPanelMobile:{width:"100%"},
 panelHeader:{minHeight:44,flexShrink:0,marginBottom:12,paddingHorizontal:3,flexDirection:"row",alignItems:"center",justifyContent:"space-between",borderBottomWidth:1,borderBottomColor:"#e4edf5"},
 searchHeader:{},
 searchTitle:{fontSize:18,fontWeight:"600",color:"#1d2633",flexShrink:1},
 panelScroll:{flex:1,minHeight:0},
 panelContent:{paddingRight:6,paddingBottom:6},
 panelContentMobile:{paddingBottom:6},
 searchFooter:{flexShrink:0,borderTopWidth:1,borderTopColor:"#e4edf5",paddingTop:10,marginTop:8},
 mapViewport:{flex:1,flexBasis:0,minHeight:0,overflow:"hidden",borderRadius:18},
 mapViewportMobile:{height:390,borderRadius:18,overflow:"hidden"},
 modeBar:{flexDirection:"row",backgroundColor:"#eef3f8",borderRadius:11,padding:3,gap:0,justifyContent:"space-between",marginBottom:14},
 modeItem:{paddingHorizontal:5,minHeight:34,justifyContent:"center",alignItems:"center",flexDirection:"row",gap:4,borderRadius:10,flexGrow:1},
 modeActive:{backgroundColor:"#fff",shadowColor:"#336191",shadowOpacity:.08,shadowRadius:4,elevation:1},
 modeText:{fontSize:12,color:"#586c80",fontWeight:"500"},modeTextActive:{fontWeight:"600",color:"#0069d2"},
 addresses:{gap:7},middleActions:{alignSelf:"flex-end",flexDirection:"row",gap:7,marginVertical:1},
 smallAction:{borderWidth:1,borderColor:"#d2e2f1",backgroundColor:"#fff",height:32,width:36,borderRadius:16,alignItems:"center",justifyContent:"center"},
 searchButton:{marginTop:0,backgroundColor:"#0071e3",borderRadius:24,minHeight:48,flexDirection:"row",justifyContent:"center",alignItems:"center",gap:11},
 searchButtonText:{color:"#fff",fontSize:14,fontWeight:"700"},
 warning:{marginTop:12,backgroundColor:"#fff7e9",borderRadius:10,padding:10,flexDirection:"row",gap:8,alignItems:"center"},
 warningText:{flex:1,fontSize:12,color:"#94602c",lineHeight:18},
 resultsHeader:{},resultsTitle:{fontWeight:"600",color:"#1d2633",fontSize:18},
 departure:{flexDirection:"row",alignItems:"center",gap:7,marginBottom:14},departureText:{fontSize:12,color:"#586c80"},departureCount:{marginLeft:"auto",fontSize:12,color:"#586c80"},
 recommended:{backgroundColor:"#f9fcff",borderRadius:15,borderWidth:1,borderColor:"#d4e4f5",padding:14,shadowColor:"#336191",shadowOpacity:.08,shadowRadius:16,elevation:2},
 recommendedBadge:{color:"#0069d2",fontWeight:"700",fontSize:10,letterSpacing:1},
 recommendedTop:{flexDirection:"row",justifyContent:"space-between",alignItems:"center",marginTop:8,flexWrap:"wrap",gap:5},duration:{fontWeight:"700",fontSize:26,color:"#1d2633"},fare:{fontWeight:"600",fontSize:14,color:"#1d2633"},
 routeSequence:{flexDirection:"row",alignItems:"center",gap:9,marginTop:10},routeSequenceText:{color:"#586c80",fontSize:12},
 routeDisclaimer:{color:"#667c92",fontSize:11,marginTop:8},
 emptyResults:{backgroundColor:"rgba(255,255,255,.86)",borderRadius:24,minHeight:200,padding:23,justifyContent:"center",alignItems:"center",gap:10},
 emptyResultsTitle:{fontWeight:"600",color:"#1d2633",fontSize:14},emptyResultsCopy:{color:"#667c92",fontSize:12,textAlign:"center",lineHeight:19},
 mapCard:{backgroundColor:"#fff",borderRadius:20,padding:12,flex:1,minWidth:0,minHeight:0,borderWidth:1,borderColor:"#d9e6f5"},
 mapCardMobile:{flex:0,width:"100%"},
 mapHeader:{},
 mapTitle:{color:"#1d2633",fontSize:18,fontWeight:"600"},mapBadge:{backgroundColor:"#fff",paddingHorizontal:11,paddingVertical:8,borderRadius:16,flexDirection:"row",alignItems:"center",gap:6},mapBadgeText:{color:"#0069d2",fontSize:12,fontWeight:"500"},
 mapBottom:{backgroundColor:"#f2f7fc",flexShrink:0,borderRadius:12,padding:10,marginTop:10,flexDirection:"row",alignItems:"center",gap:9},
 mapBottomText:{flex:1,fontSize:12,lineHeight:18,color:"#63778c"},
 demoPanel:{marginTop:18,backgroundColor:"#fff",borderRadius:23,padding:18,borderWidth:1,borderColor:"#d2e2f1"},
 demoHead:{flexDirection:"row",gap:9,alignItems:"center"},demoTitle:{fontSize:15,fontWeight:"700",color:"#1d2633",flex:1},
 demoDescription:{fontSize:12,color:"#667c92",lineHeight:19,marginTop:9},
 demoButton:{backgroundColor:"#0069d2",borderRadius:16,marginTop:13,minHeight:41,flexDirection:"row",alignItems:"center",justifyContent:"center",gap:8},
 demoButtonText:{color:"#fff",fontWeight:"700",fontSize:12},demoError:{color:"#98602a",marginTop:9,fontSize:12},
 demoResults:{marginTop:14,gap:9},demoLabel:{color:"#0069d2",fontSize:10,fontWeight:"700",letterSpacing:.7},
 demoRoute:{padding:12,backgroundColor:"#eef5fd",borderRadius:12,gap:4},
 demoRouteHeader:{flexDirection:"row",justifyContent:"space-between",alignItems:"center",gap:6},demoRouteTitle:{fontSize:12,color:"#1d2633",fontWeight:"700"},
 demoMinutes:{fontSize:16,color:"#0069d2",fontWeight:"700"},demoDetail:{fontSize:11,color:"#667c92",lineHeight:17},
 demoCost:{fontSize:12,color:"#1d2633",fontWeight:"600"},
 itineraryHeader:{marginTop:18,flexDirection:"row",justifyContent:"space-between",alignItems:"center"},
 itineraryHeading:{fontSize:13,fontWeight:"700",color:"#253750"},
 itineraryCount:{fontSize:11,color:"#657b94"},
 detailsToggle:{marginTop:10,paddingVertical:10,flexDirection:"row",justifyContent:"center",alignItems:"center",gap:6,borderTopWidth:1,borderTopColor:"#e0eafa"},
 detailsToggleText:{fontWeight:"600",fontSize:11,color:"#0069d2"},
 labSection:{marginTop:18},
 labToggle:{backgroundColor:"#f4f8fe",borderWidth:1,borderColor:"#cfdff1",borderRadius:12,paddingHorizontal:18,paddingVertical:14,flexDirection:"row",alignItems:"center",justifyContent:"space-between"},
 labToggleText:{fontSize:13,fontWeight:"600",color:"#56739a"},
 assistantArea:{flexDirection:"row",gap:14,marginTop:24,alignItems:"stretch"},assistantAreaMobile:{flexDirection:"column"},
 assistant:{flex:1,minWidth:0,backgroundColor:"rgba(255,255,255,.93)",borderRadius:25,padding:24,shadowColor:"#336191",shadowOpacity:.07,shadowRadius:20,elevation:1},
 assistantHeader:{flexDirection:"row",justifyContent:"space-between",alignItems:"center",flexWrap:"wrap",gap:12},
 assistantHeaderLeft:{flexDirection:"row",alignItems:"center",gap:11,flex:1},
 assistantTitle:{fontSize:19,fontWeight:"700",color:"#1d2633"},assistantSubtitle:{fontSize:12,color:"#586c80",marginTop:4},
 assistantTag:{fontWeight:"700",fontSize:10,letterSpacing:1,color:"#0069d2"},
 suggestions:{flexDirection:"row",gap:8,flexWrap:"wrap",marginTop:17},suggestion:{borderRadius:18,paddingHorizontal:13,paddingVertical:8,backgroundColor:"#e8f2fd"},suggestionText:{color:"#0069d2",fontSize:12,fontWeight:"500"},
 chatHistory:{minHeight:180,maxHeight:340,marginVertical:15},chatEmpty:{fontSize:12,color:"#7388a0",paddingTop:12},
 chatBubble:{borderRadius:18,padding:12,maxWidth:"90%"},chatBubbleUser:{backgroundColor:"#0071e3",alignSelf:"flex-end"},chatBubbleAi:{backgroundColor:"#eaf3fc",alignSelf:"flex-start"},
 chatBubbleText:{color:"#1d2633",fontSize:13,lineHeight:20},chatSource:{color:"#586c80",fontSize:10,marginTop:8},
 chatInput:{flexDirection:"row",alignItems:"center",minHeight:49,backgroundColor:"#f0f5fa",borderRadius:25,paddingLeft:15,paddingRight:5},
 chatField:{flex:1,color:"#1d2633",fontSize:14,paddingVertical:11},chatSend:{height:39,width:39,borderRadius:20,backgroundColor:"#0071e3",alignItems:"center",justifyContent:"center"},
 academicPanel:{width:360,flexShrink:0,borderRadius:25,padding:20,backgroundColor:"#fff",borderWidth:1,borderColor:"#d9e6f5"},academicMobile:{width:"100%"},academicHeader:{flexDirection:"row",alignItems:"center",gap:10,marginBottom:12},academicFilters:{flexDirection:"row",gap:5,marginBottom:10,flexWrap:"wrap"},academicFilter:{paddingHorizontal:10,paddingVertical:7,borderRadius:10,backgroundColor:"#f0f5fa"},academicScroll:{maxHeight:320,minHeight:100},academicQuestion:{flexDirection:"row",alignItems:"center",gap:9,paddingVertical:10,borderBottomWidth:1,borderBottomColor:"#e5edf5",paddingRight:6},academicNumber:{backgroundColor:"#e8f2fd",borderRadius:9,padding:8},
 assistantFootnote:{fontSize:10,color:"#71859b",marginTop:9},
 footer:{marginVertical:22,textAlign:"center",fontSize:11,color:"#667c92"}
});
