import React, { useEffect, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet,
 Text, TextInput, View, useWindowDimensions } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import * as Location from "expo-location";
import MapaPreview from "../components/MapaPreview";

const API = (process.env.EXPO_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
type Icon = React.ComponentProps<typeof Ionicons>["name"];
type Modal = "todos"|"ferroviario"|"onibus"|"ape";
type Endereco = {nome:string;lat:number;lon:number;fonte:string};
type Resultado = {tipo:string;fonte:string;tempo_min:number;distancia_m:number;tarifa_centavos:number|null;seguranca:{status:string};trajeto:number[][];aviso:string};
type Consulta = {resposta:string;fontes:{referencia:string;data_verificacao:string}[]};

const transportes: {id:Modal;nome:string;icone:Icon;foto:any}[] = [
 {id:"ferroviario",nome:"Trem e Metrô",icone:"train-outline",foto:require("../assets/metro_futurista.jpg")},
  {id:"onibus",nome:"Ônibus",icone:"bus-outline",foto:require("../assets/onibus_futurista.jpg")},
  {id:"ape",nome:"A pé",icone:"walk-outline",foto:require("../assets/caminhada_futurista.jpg")},
];
const sugestoesChat=["Como emitir cartão?","Quem tem direito à gratuidade?","Quais são meus direitos?","Como funciona a integração?"];

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
   if(escolhido || valor.trim().length<4){setLista([]);setMensagem("");return;}
   const controller=new AbortController();
   const timer=setTimeout(async()=>{
     setBuscando(true);setMensagem("");
     try{
       const resp=await fetch(API+"/enderecos/sugestoes?q="+encodeURIComponent(valor.trim()),{signal:controller.signal});
       if(!resp.ok){setMensagem(resp.status===429?"Aguarde um momento antes de pesquisar.":"Serviço de endereços indisponível.");return;}
       const data=await resp.json();
       setLista(Array.isArray(data.resultados)?data.resultados:[]);
       if(!data.resultados?.length)setMensagem("Nenhum endereço encontrado. Inclua cidade e número.");
     }catch(e){if(!controller.signal.aborted)setMensagem("Falha na consulta de endereços.");}
     finally{if(!controller.signal.aborted)setBuscando(false);}
   },1250);
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
   {!!lista.length && <View style={s.drop}>
     {lista.map((end,i)=><Pressable key={i} style={s.dropItem} onPress={()=>{selecionar(end);setLista([]);setMensagem("");}} accessibilityRole="button">
       <Icone name="location-outline" color="#5b67b2" size={17}/>
       <Text style={s.dropText} numberOfLines={2}>{end.nome}</Text>
     </Pressable>)}
   </View>}
   {!!mensagem && !escolhido && <Text style={s.hint}>{mensagem}</Text>}
 </View>;
}

export default function Home(){
 const {width}=useWindowDimensions();const mobile=width<820;
 const [modal,setModal]=useState<Modal>("todos");
 const [origem,setOrigem]=useState("");const [destino,setDestino]=useState("");
 const [origemGeo,setOrigemGeo]=useState<Endereco|null>(null);const [destinoGeo,setDestinoGeo]=useState<Endereco|null>(null);
 const [localizando,setLocalizando]=useState(false);const [carregando,setCarregando]=useState(false);
 const [erro,setErro]=useState("");const [resultado,setResultado]=useState<Resultado|null>(null);
 const [chatTexto,setChatTexto]=useState("");const [chat,setChat]=useState<{autor:"pessoa"|"agente";texto:string;fonte?:string}[]>([]);
 const [chatCarregando,setChatCarregando]=useState(false);
 const [fotoBase,setFotoBase]=useState(false);

 const pontos=[origemGeo,destinoGeo].filter((p):p is Endereco=>p!==null);
 const lat=origemGeo?.lat||destinoGeo?.lat||-23.55,lon=origemGeo?.lon||destinoGeo?.lon||-46.63;
 const bbox=[lon-.06,lat-.06,lon+.06,lat+.06].join("%2C");
 const preview="https://www.openstreetmap.org/export/embed.html?bbox="+bbox+"&layer=mapnik";

 const atualizarOrigem=(t:string)=>{setOrigem(t);setOrigemGeo(null);setResultado(null);setErro("");};
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
   if(modal!=="ape"){
     setErro("Para ônibus, trem e metrô, ainda estamos conectando horários e rotas oficiais. Os endereços selecionados já aparecem no mapa, mas não há previsão de viagem validada.");
     return;
   }
   setCarregando(true);
   try{
     const r=await fetch(API+"/rotas/reais",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({
       origem:{lat:origemGeo.lat,lon:origemGeo.lon},destino:{lat:destinoGeo.lat,lon:destinoGeo.lon},modal:"ape",
     })});
     const data=await r.json().catch(()=>({}));
     if(!r.ok)throw new Error(data.detail||"Serviço de rotas indisponível.");
     setResultado(data);
   }catch(e){setErro(e instanceof Error?e.message:"Não foi possível calcular a rota.");}
   finally{setCarregando(false);}
 }
 async function perguntar(pergunta=chatTexto){
   const texto=pergunta.trim();if(!texto || chatCarregando)return;
   setChatTexto("");setChat(c=>[...c,{autor:"pessoa",texto}]);setChatCarregando(true);
   try{
     const r=await fetch(API+"/consultar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({pergunta:texto,modelo:"B"})});
     if(!r.ok)throw new Error("Serviço de consultas indisponível");
     const data:Consulta=await r.json();
     const fontes=(data.fontes||[]).map(f=>f.referencia).join(" · ");
     setChat(c=>[...c,{autor:"agente",texto:data.resposta,fonte:fontes||undefined}]);
   }catch{setChat(c=>[...c,{autor:"agente",texto:"Não foi possível consultar as orientações neste momento."}]);}
   finally{setChatCarregando(false);}
 }

 return <ScrollView style={v.bg} contentContainerStyle={v.page}>
   <View style={v.nav}>
     <Text style={[v.navBrand,mobile&&v.navBrandMobile]}>Citizen Tech <Text style={v.navBrandAccent}>Mobilidade Urbana</Text></Text>
     {!mobile&&<View style={v.navActive}><Text style={v.navActiveText}>Planejar trajeto</Text></View>}
     <Text style={v.navMeta}>Global Solution · 2026</Text>
   </View>

   <View style={v.container}>
     <View style={[v.intro,mobile&&v.introMobile]}>
       <Text style={v.eyebrow}>MENOS COMPLICAÇÃO. MAIS CIDADE.</Text>
       <Text style={[v.heading,mobile&&v.headingMobile]}>Seu próximo destino começa aqui.</Text>
       <Text style={v.subtitle}>Combine metrô, ônibus e caminhada. Encontre o melhor caminho para você.</Text>
       {!mobile&&<View style={v.cityBadge}><Icone name="location-outline" size={17} color="#0069d2"/><Text style={v.cityText}>São Paulo, SP</Text></View>}
     </View>

     <View style={[v.main,mobile&&v.mainMobile]}>
       <View style={[v.sidebar,mobile&&v.sidebarMobile]}>
         <View style={v.searchCard}>
           <Text style={v.searchTitle}>Para onde vamos?</Text>
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
           </View>
           <Pressable onPress={planejar} disabled={carregando} style={v.searchButton} accessibilityRole="button">
             {carregando?<ActivityIndicator color="#fff" size="small"/>:<Icone name="navigate-outline" size={18} color="#fff"/>}
             <Text style={v.searchButtonText}>{carregando?"Calculando...":"Encontrar trajeto"}</Text>
             <Icone name="arrow-forward-outline" size={18} color="#fff"/>
           </Pressable>
           {!!erro&&<View style={v.warning}><Icone name="information-circle-outline" size={17} color="#94602c"/><Text style={v.warningText}>{erro}</Text></View>}
         </View>

         <View style={v.resultsHeader}><Text style={v.resultsTitle}>Trajetos sugeridos</Text><Icone name="options-outline" size={20} color="#667c92"/></View>
         <View style={v.departure}><Icone name="time-outline" size={15} color="#667c92"/><Text style={v.departureText}>Saída agora</Text><Text style={v.departureCount}>{resultado?"1 opção validada":"Aguardando busca"}</Text></View>
         {resultado?<View style={v.recommended}>
            <Text style={v.recommendedBadge}>TRAJETO DISPONÍVEL · A PÉ</Text>
            <View style={v.recommendedTop}><Text style={v.duration}>{resultado.tempo_min} min</Text><Text style={v.fare}>Gratuito</Text></View>
            <View style={v.routeSequence}><Icone name="walk-outline" color="#0069d2" size={20}/><Text style={v.routeSequenceText}>{(resultado.distancia_m/1000).toFixed(1)} km · {resultado.fonte}</Text></View>
            <Text style={v.routeDisclaimer}>Estimativa de caminhada; segurança não verificada.</Text>
          </View>:<View style={v.emptyResults}><Icone name="git-compare-outline" size={27} color="#8ba2bd"/><Text style={v.emptyResultsTitle}>Seu trajeto aparecerá aqui</Text><Text style={v.emptyResultsCopy}>Selecione endereços sugeridos e um modo de transporte para consultar as opções disponíveis. Os trajetos de transporte público ainda não possuem dados operacionais integrados.</Text></View>}
       </View>

       <View style={[v.mapCard,mobile&&v.mapCardMobile]}>
         <View style={v.mapHeader}><Text style={v.mapTitle}>Mapa do trajeto</Text><View style={v.mapBadge}><Icone name="map-outline" size={15} color="#0069d2"/><Text style={v.mapBadgeText}>Mapa interativo</Text></View></View>
         <MapaPreview url={preview} pontos={pontos} trajeto={resultado?.trajeto} height={mobile?390:560}/>
         <View style={v.mapBottom}>
           <Icone name="information-circle-outline" color="#63778c" size={17}/>
           <Text style={v.mapBottomText}>{resultado?"Percurso a pé calculado a partir da origem e do destino selecionados.":"Escolha origem e destino para visualizar os pontos no mapa. Rotas reais de metrô e ônibus ainda não estão disponíveis."}</Text>
         </View>
       </View>
     </View>

     <View style={v.assistant}>
       <View style={v.assistantHeader}>
         <View style={v.assistantHeaderLeft}><Icone name="chatbubble-ellipses-outline" color="#0069d2" size={23}/><View style={{flex:1}}><Text style={v.assistantTitle}>Pergunte ao agente de IA</Text><Text style={v.assistantSubtitle}>Orientações sobre cartões, benefícios, integração e transporte</Text></View></View>
         <Text style={v.assistantTag}>ASSISTENTE CIDADÃO</Text>
       </View>
       <View style={v.suggestions}>{sugestoesChat.map(t=><Pressable key={t} style={v.suggestion} onPress={()=>perguntar(t)}><Text style={v.suggestionText}>{t}</Text></Pressable>)}</View>
       <ScrollView style={v.chatHistory} nestedScrollEnabled><View style={{gap:10}}>{chat.length===0?<Text style={v.chatEmpty}>Selecione uma sugestão ou escreva sua dúvida sobre mobilidade.</Text>:chat.map((m,i)=><View key={i} style={[v.chatBubble,m.autor==="pessoa"?v.chatBubbleUser:v.chatBubbleAi]}><Text style={[v.chatBubbleText,m.autor==="pessoa"&&{color:"#fff"}]}>{m.texto}</Text>{!!m.fonte&&<Text style={v.chatSource}>{m.fonte}</Text>}</View>)}</View></ScrollView>
       <View style={v.chatInput}><TextInput accessibilityLabel="Pergunta para o agente de IA" value={chatTexto} onChangeText={setChatTexto} placeholder="Escreva sua pergunta..." placeholderTextColor="#9baec2" onSubmitEditing={()=>perguntar()} returnKeyType="send" style={v.chatField}/><Pressable style={v.chatSend} onPress={()=>perguntar()} accessibilityLabel="Enviar pergunta">{chatCarregando?<ActivityIndicator color="#fff"/>:<Icone name="send" size={18} color="#fff"/>}</Pressable></View>
       <Text style={v.assistantFootnote}>Respostas baseadas nas informações disponíveis na base acadêmica, com referências quando disponíveis.</Text>
     </View>

     <Text style={v.footer}>Citizen Tech Mobilidade Urbana · FIAP Global Solution 2026 · Indicadores de segurança não verificados; rotas reais de transporte público em desenvolvimento.</Text>
   </View>
 </ScrollView>;
}

const s=StyleSheet.create({
 autocomplete:{position:"relative"},
 inputLabel:{fontSize:10,fontWeight:"800",color:"#586c80",marginBottom:6,letterSpacing:.8},
 inputWrap:{minHeight:58,borderRadius:14,backgroundColor:"#f0f5fa",flexDirection:"row",alignItems:"center",paddingHorizontal:14,gap:9},
 textInput:{flex:1,fontSize:14,fontWeight:"500",color:"#1d2633",paddingVertical:10,minWidth:0},
 drop:{backgroundColor:"#fff",borderWidth:1,borderColor:"#c7ddeb",borderRadius:12,marginTop:4,overflow:"hidden"},
 dropItem:{padding:11,flexDirection:"row",gap:8,borderBottomWidth:1,borderBottomColor:"#f0f5fa",alignItems:"center"},
 dropText:{color:"#1d2633",fontSize:13,flex:1},
 hint:{fontSize:11,color:"#71859b",marginTop:5}
});

const v=StyleSheet.create({
 bg:{flex:1,backgroundColor:"#dfefff"},
 page:{minHeight:"100%"},
 nav:{backgroundColor:"rgba(247,251,255,0.90)",minHeight:88,paddingHorizontal:48,paddingVertical:20,borderBottomWidth:1,borderBottomColor:"#bfd6ec",flexDirection:"row",alignItems:"center",gap:30,flexWrap:"wrap"},
 navBrand:{fontSize:25,fontWeight:"800",letterSpacing:-.9,color:"#1d2633"},navBrandMobile:{fontSize:19},navBrandAccent:{fontWeight:"500",color:"#0069d2"},
 navActive:{backgroundColor:"#dcebfa",borderRadius:22,paddingHorizontal:18,paddingVertical:13},navActiveText:{color:"#0069d2",fontSize:14,fontWeight:"700"},navMeta:{fontSize:11,color:"#62758a",marginLeft:"auto"},
 container:{maxWidth:1440,width:"100%",alignSelf:"center",paddingHorizontal:48,paddingBottom:28},
 intro:{minHeight:182,paddingTop:34,justifyContent:"center",position:"relative",paddingBottom:23},introMobile:{paddingTop:24,minHeight:0},
 eyebrow:{color:"#0069d2",fontSize:11,fontWeight:"800",letterSpacing:1.7,marginBottom:12},
 heading:{color:"#1d2633",fontWeight:"800",fontSize:42,letterSpacing:-1.5,lineHeight:53},headingMobile:{fontSize:29,lineHeight:38},
 subtitle:{color:"#586c80",fontSize:15,marginTop:7,lineHeight:22},
 cityBadge:{position:"absolute",right:0,top:70,flexDirection:"row",alignItems:"center",gap:8,backgroundColor:"rgba(255,255,255,.7)",borderRadius:24,paddingHorizontal:16,paddingVertical:13},cityText:{color:"#1d2633",fontSize:13,fontWeight:"600"},
 main:{flexDirection:"row",alignItems:"stretch",gap:24},mainMobile:{flexDirection:"column"},
 sidebar:{width:408,maxWidth:"100%"},sidebarMobile:{width:"100%"},
 searchCard:{backgroundColor:"rgba(255,255,255,.96)",padding:24,borderRadius:24,shadowColor:"#336191",shadowOpacity:.08,shadowRadius:26,elevation:2},
 searchTitle:{fontSize:21,fontWeight:"800",color:"#1d2633",marginBottom:16},
 modeBar:{flexDirection:"row",backgroundColor:"#eef3f8",borderRadius:13,padding:4,gap:1,justifyContent:"space-between",marginBottom:16},
 modeItem:{paddingHorizontal:9,minHeight:34,justifyContent:"center",alignItems:"center",flexDirection:"row",gap:4,borderRadius:10,flexGrow:1},
 modeActive:{backgroundColor:"#fff",shadowColor:"#336191",shadowOpacity:.08,shadowRadius:4,elevation:1},
 modeText:{fontSize:12,color:"#586c80",fontWeight:"500"},modeTextActive:{fontWeight:"700",color:"#0069d2"},
 addresses:{gap:7},middleActions:{alignSelf:"flex-end",flexDirection:"row",gap:7,marginVertical:1},
 smallAction:{borderWidth:1,borderColor:"#d2e2f1",backgroundColor:"#fff",height:32,width:36,borderRadius:16,alignItems:"center",justifyContent:"center"},
 searchButton:{marginTop:17,backgroundColor:"#0071e3",borderRadius:24,minHeight:48,flexDirection:"row",justifyContent:"center",alignItems:"center",gap:11},
 searchButtonText:{color:"#fff",fontSize:14,fontWeight:"800"},
 warning:{marginTop:12,backgroundColor:"#fff7e9",borderRadius:10,padding:10,flexDirection:"row",gap:8,alignItems:"center"},
 warningText:{flex:1,fontSize:12,color:"#94602c",lineHeight:18},
 resultsHeader:{marginTop:24,marginBottom:11,flexDirection:"row",alignItems:"center",justifyContent:"space-between"},resultsTitle:{fontWeight:"800",color:"#1d2633",fontSize:18},
 departure:{flexDirection:"row",alignItems:"center",gap:7,marginBottom:14},departureText:{fontSize:12,color:"#586c80"},departureCount:{marginLeft:"auto",fontSize:12,color:"#586c80"},
 recommended:{backgroundColor:"#f6faff",borderRadius:22,borderWidth:1.5,borderColor:"#6ca9eb",padding:20,shadowColor:"#336191",shadowOpacity:.08,shadowRadius:16,elevation:2},
 recommendedBadge:{color:"#0069d2",fontWeight:"800",fontSize:10,letterSpacing:1},
 recommendedTop:{flexDirection:"row",justifyContent:"space-between",alignItems:"center",marginTop:6},duration:{fontWeight:"800",fontSize:26,color:"#1d2633"},fare:{fontWeight:"700",fontSize:14,color:"#1d2633"},
 routeSequence:{flexDirection:"row",alignItems:"center",gap:9,marginTop:10},routeSequenceText:{color:"#586c80",fontSize:12},
 routeDisclaimer:{color:"#667c92",fontSize:11,marginTop:8},
 emptyResults:{backgroundColor:"rgba(255,255,255,.86)",borderRadius:24,minHeight:200,padding:23,justifyContent:"center",alignItems:"center",gap:10},
 emptyResultsTitle:{fontWeight:"700",color:"#1d2633",fontSize:14},emptyResultsCopy:{color:"#667c92",fontSize:12,textAlign:"center",lineHeight:19},
 mapCard:{backgroundColor:"#eff5fb",borderRadius:26,padding:15,flex:1,minWidth:0,borderWidth:1,borderColor:"rgba(255,255,255,.8)",shadowColor:"#336191",shadowOpacity:.10,shadowRadius:36,elevation:2},
 mapCardMobile:{flex:0,width:"100%"},
 mapHeader:{flexDirection:"row",alignItems:"center",justifyContent:"space-between",marginBottom:13,paddingHorizontal:2},
 mapTitle:{color:"#1d2633",fontSize:18,fontWeight:"800"},mapBadge:{backgroundColor:"#fff",paddingHorizontal:11,paddingVertical:8,borderRadius:16,flexDirection:"row",alignItems:"center",gap:6},mapBadgeText:{color:"#0069d2",fontSize:12,fontWeight:"600"},
 mapBottom:{backgroundColor:"rgba(255,255,255,.88)",borderRadius:15,padding:13,marginTop:12,flexDirection:"row",alignItems:"center",gap:9},
 mapBottomText:{flex:1,fontSize:12,lineHeight:18,color:"#63778c"},
 assistant:{marginTop:24,backgroundColor:"rgba(255,255,255,.93)",borderRadius:25,padding:24,shadowColor:"#336191",shadowOpacity:.07,shadowRadius:20,elevation:1},
 assistantHeader:{flexDirection:"row",justifyContent:"space-between",alignItems:"center",flexWrap:"wrap",gap:12},
 assistantHeaderLeft:{flexDirection:"row",alignItems:"center",gap:11,flex:1},
 assistantTitle:{fontSize:19,fontWeight:"800",color:"#1d2633"},assistantSubtitle:{fontSize:12,color:"#586c80",marginTop:4},
 assistantTag:{fontWeight:"800",fontSize:10,letterSpacing:1,color:"#0069d2"},
 suggestions:{flexDirection:"row",gap:8,flexWrap:"wrap",marginTop:17},suggestion:{borderRadius:18,paddingHorizontal:13,paddingVertical:8,backgroundColor:"#e8f2fd"},suggestionText:{color:"#0069d2",fontSize:12,fontWeight:"600"},
 chatHistory:{minHeight:65,maxHeight:230,marginVertical:15},chatEmpty:{fontSize:12,color:"#7388a0",paddingTop:12},
 chatBubble:{borderRadius:18,padding:12,maxWidth:"90%"},chatBubbleUser:{backgroundColor:"#0071e3",alignSelf:"flex-end"},chatBubbleAi:{backgroundColor:"#eaf3fc",alignSelf:"flex-start"},
 chatBubbleText:{color:"#1d2633",fontSize:13,lineHeight:20},chatSource:{color:"#586c80",fontSize:10,marginTop:8},
 chatInput:{flexDirection:"row",alignItems:"center",minHeight:49,backgroundColor:"#f0f5fa",borderRadius:25,paddingLeft:15,paddingRight:5},
 chatField:{flex:1,color:"#1d2633",fontSize:14,paddingVertical:11},chatSend:{height:39,width:39,borderRadius:20,backgroundColor:"#0071e3",alignItems:"center",justifyContent:"center"},
 assistantFootnote:{fontSize:10,color:"#71859b",marginTop:9},
 footer:{marginVertical:22,textAlign:"center",fontSize:11,color:"#667c92"}
});
