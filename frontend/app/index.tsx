import React, { useEffect, useState } from "react";
import { ActivityIndicator, ImageBackground, Pressable, ScrollView, StyleSheet,
 Text, TextInput, View, useWindowDimensions } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import * as Location from "expo-location";
import MapaPreview from "../components/MapaPreview";

const API = (process.env.EXPO_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
type Icon = React.ComponentProps<typeof Ionicons>["name"];
type Modal = "ferroviario"|"onibus"|"ape";
type Endereco = {nome:string;lat:number;lon:number;fonte:string};
type Resultado = {tipo:string;fonte:string;tempo_min:number;distancia_m:number;tarifa_centavos:number|null;seguranca:{status:string};trajeto:number[][];aviso:string};
type Consulta = {resposta:string;fontes:{referencia:string;data_verificacao:string}[]};

const transportes: {id:Modal;nome:string;icone:Icon;foto:string}[] = [
 {id:"ferroviario",nome:"Trem e Metrô",icone:"train-outline",foto:"https://images.unsplash.com/photo-1519608487953-e999c86e7455?w=1100&q=85"},
 {id:"onibus",nome:"Ônibus",icone:"bus-outline",foto:"https://images.unsplash.com/photo-1570125909232-eb263c188f7e?w=1100&q=85"},
 {id:"ape",nome:"A pé",icone:"walk-outline",foto:"https://images.unsplash.com/photo-1473448912268-2022ce9509d8?w=1100&q=85"},
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
     <Icone name="location-outline" size={20}/>
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
 const [modal,setModal]=useState<Modal>("ferroviario");
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
 return <ScrollView style={s.bg} contentContainerStyle={s.page}><View style={s.container}>
   <View style={s.header}>
     <View style={s.logo}><Icone name="layers-outline" color="#fff" size={22}/></View>
     <View><Text style={s.brand}>Citizen Tech</Text><Text style={s.brandSub}>Mobilidade Urbana</Text></View>
     <Text style={s.headerRight}>Global Solution · 2026</Text>
   </View>
   <View style={[s.hero,mobile&&s.heroMobile]}>
     <View style={s.heroContent}>
       <Text style={s.eyebrow}>CIDADANIA • TECNOLOGIA • MOBILIDADE</Text>
       <Text style={[s.title,mobile&&s.titleMobile]}>O melhor caminho começa <Text style={s.titleAccent}>com informação.</Text></Text>
       <Text style={s.lead}>Encontre destinos, explore opções de transporte e esclareça suas dúvidas com uma experiência simples, conectada e feita para a cidade.</Text>
       <View style={s.heroChips}><View style={s.heroChip}><Icone name="location-outline" size={15}/><Text style={s.heroChipText}>Endereços inteligentes</Text></View><View style={s.heroChip}><Icone name="shield-checkmark-outline" size={15}/><Text style={s.heroChipText}>Fontes identificadas</Text></View></View>
     </View>
     {!mobile&&<View style={s.heroGraphic}><View style={s.glowA}/><View style={s.glowB}/><View style={s.circuitCircle}><Icone name="planet-outline" color="#5a59c5" size={62}/></View><View style={s.heroGraphicTag}><Icone name="sparkles" size={18}/><Text style={s.heroGraphicText}>Cidade conectada</Text></View></View>}
   </View>
   <View style={s.planner}>
     <View style={s.plannerHeading}><Icone name="navigate-outline" size={23}/><Text style={s.sectionTitle}>Planeje sua rota</Text></View>
     <Text style={s.sectionSub}>Digite um endereço e escolha uma das sugestões para marcar a origem e o destino.</Text>
     <View style={[s.inputs,mobile&&s.inputsMobile]}>
       <View style={s.flexField}><CampoEndereco titulo="Ponto de partida" valor={origem} escolhido={origemGeo} mudar={atualizarOrigem} selecionar={e=>{setOrigem(e.nome);setOrigemGeo(e);setResultado(null);}} placeholder="Rua, número, bairro ou estação"/></View>
       <View style={s.actionsOrigin}><Pressable onPress={obterPosicao} accessibilityLabel="Usar localização atual" style={s.locationButton}>{localizando?<ActivityIndicator color="#665ec4"/>:<Icone name="locate-outline" size={21}/>}</Pressable><Pressable onPress={()=>{setOrigem(destino);setDestino(origem);setOrigemGeo(destinoGeo);setDestinoGeo(origemGeo);setResultado(null);}} style={s.locationButton} accessibilityLabel="Inverter origem e destino"><Icone name="swap-horizontal" size={21}/></Pressable></View>
       <View style={s.flexField}><CampoEndereco titulo="Destino" valor={destino} escolhido={destinoGeo} mudar={atualizarDestino} selecionar={e=>{setDestino(e.nome);setDestinoGeo(e);setResultado(null);}} placeholder="Ex.: Rua Maracá, 270, São Paulo"/></View>
     </View>
     <Pressable onPress={planejar} style={s.planButton} disabled={carregando} accessibilityRole="button"><Icone name="navigate-outline" color="#fff" size={20}/><Text style={s.planButtonText}>{carregando?"Calculando percurso...":"Traçar rota no mapa"}</Text></Pressable>
     {!!erro&&<View style={s.warning}><Icone name="information-circle-outline" color="#986b2d"/><Text style={s.warningText}>{erro}</Text></View>}
   </View>
   <Text style={s.modesTitle}>Escolha como deseja se deslocar</Text>
   <View style={[s.transportRow,mobile&&s.transportMobile]}>
     {transportes.map(t=><Pressable key={t.id} style={[s.transportCard,modal===t.id&&s.transportActive]} onPress={()=>{setModal(t.id);setResultado(null);setErro("");}} accessibilityRole="button" accessibilityState={{selected:modal===t.id}}>
       <ImageBackground source={{uri:t.foto}} style={s.transportPhoto} imageStyle={s.transportImage}>
         <View style={s.transportShade}/>
         <View style={s.transportLabel}><Icone name={t.icone} color="#fff" size={25}/><Text style={s.transportText}>{t.nome}</Text><Icone name="chevron-forward-circle" color="#fff" size={23}/></View>
       </ImageBackground>
     </Pressable>)}
   </View>
   <View style={[s.content,mobile&&s.contentMobile]}>
     <View style={s.chatPanel}>
       <View style={s.chatHeader}><View style={s.chatIcon}><Icone name="sparkles-outline" color="#655aca" size={26}/></View><View style={{flex:1}}><Text style={s.chatTitle}>Seu assistente de mobilidade</Text><Text style={s.chatIntro}>Informações sobre transporte, cartões, benefícios e direitos.</Text></View></View>
       <View style={s.suggestions}>{sugestoesChat.map(t=><Pressable key={t} style={s.suggestion} onPress={()=>perguntar(t)}><Text style={s.suggestionText}>{t}</Text></Pressable>)}</View>
       <ScrollView style={s.chatHistory} nestedScrollEnabled><View style={{gap:9}}>{chat.length===0?<Text style={s.empty}>Escolha uma sugestão ou digite sua pergunta.</Text>:chat.map((m,i)=><View key={i} style={[s.bubble,m.autor==="pessoa"?s.bubbleUser:s.bubbleAi]}><Text style={[s.bubbleText,m.autor==="pessoa"&&{color:"#fff"}]}>{m.texto}</Text>{m.fonte&&<Text style={s.source}>{m.fonte}</Text>}</View>)}</View></ScrollView>
       <View style={s.chatInput}><TextInput accessibilityLabel="Pergunta para o assistente" value={chatTexto} onChangeText={setChatTexto} style={s.chatTextInput} placeholder="Pergunte sobre sua mobilidade..." placeholderTextColor="#959eb9" onSubmitEditing={()=>perguntar()} returnKeyType="send"/><Pressable onPress={()=>perguntar()} style={s.send}>{chatCarregando?<ActivityIndicator color="#fff"/>:<Icone name="send" color="#fff" size={19}/>}</Pressable></View>
       <Text style={s.disclaimer}>Orientações limitadas às fontes verificadas na base acadêmica.</Text>
     </View>
     <View style={s.mapPanel}>
       <View style={s.mapHeading}><Text style={s.mapTitle}>Mapa da região</Text><View style={s.mapTag}><Icone name="map-outline" size={15}/><Text style={s.mapTagText}>Mapa interativo</Text></View></View>
       <MapaPreview url={preview} pontos={pontos} trajeto={resultado?.trajeto}/>
       {resultado?<View style={s.result}>
         <Text style={s.resultHeading}>Rota a pé · {resultado.fonte}</Text>
         <View style={s.stats}><View style={s.stat}><Text style={s.statSmall}>TEMPO</Text><Text style={s.statValue}>{resultado.tempo_min} min</Text></View><View style={s.stat}><Text style={s.statSmall}>DISTÂNCIA</Text><Text style={s.statValue}>{(resultado.distancia_m/1000).toFixed(1)} km</Text></View><View style={s.stat}><Text style={s.statSmall}>TARIFA</Text><Text style={s.statValue}>Gratuito</Text></View></View>
         <View style={s.safetyInfo}><Icone name="shield-outline" size={17}/><Text style={s.safetyInfoText}>Segurança: não verificada. Não há dados de ocorrências integrados à rota.</Text></View>
         <Text style={s.mapFoot}>Estimativa de caminhada, não inclui trânsito ou alterações da via.</Text>
       </View>:<Text style={s.mapFoot}>Selecione dois endereços para ver os marcadores. Rotas reais de ônibus, metrô e trem precisam de dados operacionais, ainda não integrados.</Text>}
     </View>
   </View>
   <View style={s.safetyBlock}><Icone name="shield-checkmark-outline" size={29}/><View style={{flex:1}}><Text style={s.safetyTitle}>Indicadores de segurança por região</Text><Text style={s.safetyCopy}>Em preparação: dados agregados de ocorrências, com fonte, período e limitações.</Text></View><Text style={s.pending}>Em desenvolvimento</Text></View>
   <Text style={s.footer}>Citizen Tech Mobilidade Urbana • Projeto acadêmico FIAP. Informações de segurança não verificadas e rotas de transporte público ainda não operacionais.</Text>
 </View></ScrollView>;
}

const s=StyleSheet.create({
 bg:{flex:1,backgroundColor:"#edf1fc"},page:{padding:20,alignItems:"center"},container:{width:"100%",maxWidth:1240},
 header:{flexDirection:"row",alignItems:"center",gap:12,marginBottom:19},logo:{width:42,height:42,backgroundColor:"#5e62be",borderRadius:11,alignItems:"center",justifyContent:"center"},brand:{fontWeight:"800",color:"#253c80",fontSize:19},brandSub:{color:"#6b7aa8",fontSize:13},headerRight:{marginLeft:"auto",fontSize:11,color:"#8190b6",fontWeight:"600"},
 hero:{backgroundColor:"#dde7fd",borderRadius:13,flexDirection:"row",padding:29,minHeight:228,overflow:"hidden"},heroMobile:{padding:21},heroContent:{flex:1},eyebrow:{fontSize:10,letterSpacing:2,fontWeight:"800",color:"#626bb5",marginBottom:11},title:{fontSize:35,lineHeight:43,fontWeight:"800",color:"#273b79",maxWidth:750},titleMobile:{fontSize:27,lineHeight:34},titleAccent:{color:"#7462cb"},lead:{fontSize:14,color:"#68799f",lineHeight:22,maxWidth:715,marginTop:12},heroChips:{flexDirection:"row",flexWrap:"wrap",gap:10,marginTop:17},heroChip:{backgroundColor:"#fff",borderRadius:10,paddingVertical:7,paddingHorizontal:10,flexDirection:"row",alignItems:"center",gap:6},heroChipText:{fontSize:11,color:"#6072a6",fontWeight:"700"},
 heroGraphic:{width:235,alignItems:"center",justifyContent:"center"},glowA:{position:"absolute",width:182,height:182,backgroundColor:"#ccd7ff",borderRadius:91},glowB:{position:"absolute",width:140,height:140,backgroundColor:"#e9eaff",borderRadius:70},circuitCircle:{width:110,height:110,alignItems:"center",justifyContent:"center",borderRadius:55,backgroundColor:"#fff",borderWidth:1,borderColor:"#ccd0f7"},heroGraphicTag:{position:"absolute",bottom:17,right:0,backgroundColor:"#fff",padding:10,borderRadius:10,flexDirection:"row",gap:7,alignItems:"center"},heroGraphicText:{fontSize:11,color:"#5664ae",fontWeight:"800"},
 planner:{backgroundColor:"#fff",padding:22,borderRadius:13,marginTop:15},plannerHeading:{flexDirection:"row",alignItems:"center",gap:9},sectionTitle:{fontSize:21,color:"#303f7b",fontWeight:"800"},sectionSub:{fontSize:13,color:"#8290ab",marginTop:8,marginBottom:15},inputs:{flexDirection:"row",alignItems:"flex-start",gap:9},inputsMobile:{flexWrap:"wrap"},flexField:{flex:1,minWidth:220},autocomplete:{position:"relative"},inputLabel:{fontSize:11,fontWeight:"700",color:"#596ba0",marginBottom:7},inputWrap:{minHeight:51,borderRadius:10,borderWidth:1,borderColor:"#dbe2f4",backgroundColor:"#fafbff",flexDirection:"row",alignItems:"center",gap:8,paddingHorizontal:12},textInput:{flex:1,fontSize:14,color:"#31447a",paddingVertical:10,minWidth:20},actionsOrigin:{flexDirection:"row",gap:7,marginTop:19},locationButton:{backgroundColor:"#edf0fb",height:48,width:42,alignItems:"center",justifyContent:"center",borderRadius:9},drop:{backgroundColor:"#fff",borderWidth:1,borderColor:"#c9d2ec",borderRadius:10,marginTop:4,overflow:"hidden"},dropItem:{padding:11,flexDirection:"row",gap:8,borderBottomWidth:1,borderBottomColor:"#f1f3f9",alignItems:"center"},dropText:{color:"#3d5387",fontSize:13,flex:1},hint:{fontSize:11,color:"#8993ad",marginTop:5},planButton:{backgroundColor:"#5663ba",borderRadius:10,paddingHorizontal:22,paddingVertical:14,marginTop:15,alignSelf:"flex-start",flexDirection:"row",alignItems:"center",gap:9},planButtonText:{color:"#fff",fontWeight:"800",fontSize:14},warning:{marginTop:12,padding:12,borderRadius:9,backgroundColor:"#fff5e8",flexDirection:"row",gap:8,alignItems:"center"},warningText:{fontSize:12,color:"#976e3a",flex:1,lineHeight:19},
 modesTitle:{fontSize:16,color:"#394c81",fontWeight:"800",marginTop:21,marginBottom:10},transportRow:{flexDirection:"row",gap:14},transportMobile:{flexWrap:"wrap"},transportCard:{flex:1,minWidth:220,height:168,borderWidth:2,borderColor:"transparent",borderRadius:11,overflow:"hidden"},transportActive:{borderColor:"#6b61c6"},transportPhoto:{height:"100%",justifyContent:"flex-end"},transportImage:{borderRadius:8},transportShade:{backgroundColor:"rgba(28,39,90,.78)",height:69,position:"absolute",bottom:0,left:0,right:0},transportLabel:{flexDirection:"row",alignItems:"center",gap:12,padding:15},transportText:{color:"#fff",fontSize:20,fontWeight:"800",flex:1},
 content:{flexDirection:"row",gap:14,marginTop:18,alignItems:"stretch"},contentMobile:{flexWrap:"wrap"},chatPanel:{flex:1,minWidth:290,borderRadius:29,backgroundColor:"#faf9ff",borderColor:"#deddfa",borderWidth:1,padding:20},chatHeader:{flexDirection:"row",gap:12,alignItems:"center"},chatIcon:{width:47,height:47,borderRadius:24,backgroundColor:"#e8e5ff",alignItems:"center",justifyContent:"center"},chatTitle:{fontSize:18,color:"#34457a",fontWeight:"800"},chatIntro:{color:"#8790ac",fontSize:12,marginTop:6,lineHeight:17},suggestions:{flexDirection:"row",flexWrap:"wrap",gap:7,marginTop:17},suggestion:{backgroundColor:"#eceefe",paddingVertical:8,paddingHorizontal:12,borderRadius:23},suggestionText:{fontSize:12,color:"#5964a7"},chatHistory:{maxHeight:230,minHeight:60,marginVertical:13},empty:{color:"#8795b3",fontSize:13},bubble:{padding:11,maxWidth:"90%",borderRadius:18},bubbleUser:{backgroundColor:"#6666bd",alignSelf:"flex-end"},bubbleAi:{backgroundColor:"#e9ecfb",alignSelf:"flex-start"},bubbleText:{color:"#45598b",fontSize:13,lineHeight:20},source:{fontSize:10,color:"#667bb1",marginTop:5},chatInput:{flexDirection:"row",alignItems:"center",backgroundColor:"#fff",borderRadius:29,borderWidth:1,borderColor:"#cfd5f2",paddingLeft:15,paddingRight:5,minHeight:51},chatTextInput:{flex:1,fontSize:13,color:"#354777",paddingVertical:12},send:{width:40,height:40,backgroundColor:"#7571d2",borderRadius:22,alignItems:"center",justifyContent:"center"},disclaimer:{fontSize:10,color:"#9ba6c0",marginTop:9},
 mapPanel:{flex:1.13,minWidth:290,backgroundColor:"#fff",borderRadius:12,padding:13},mapHeading:{flexDirection:"row",alignItems:"center",justifyContent:"space-between",marginBottom:11},mapTitle:{fontSize:18,fontWeight:"800",color:"#344475"},mapTag:{backgroundColor:"#eeedff",borderRadius:10,padding:8,flexDirection:"row",gap:6,alignItems:"center"},mapTagText:{fontSize:11,color:"#6664ad"},mapFoot:{color:"#8c97ae",fontSize:11,lineHeight:19,marginTop:12},result:{backgroundColor:"#f5f6ff",borderRadius:11,padding:12,marginTop:9},resultHeading:{fontSize:13,color:"#485995",fontWeight:"800"},stats:{flexDirection:"row",flexWrap:"wrap",gap:8,marginTop:10},stat:{flex:1,minWidth:88,backgroundColor:"#fff",borderRadius:8,padding:9},statSmall:{fontSize:10,color:"#8490ad",fontWeight:"700"},statValue:{fontSize:17,color:"#394784",fontWeight:"800",marginTop:6},safetyInfo:{flexDirection:"row",alignItems:"center",gap:9,marginTop:11},safetyInfoText:{color:"#66759d",fontSize:11,lineHeight:18,flex:1},
 safetyBlock:{backgroundColor:"#e4e8fb",borderRadius:12,marginTop:18,padding:16,flexDirection:"row",gap:14,alignItems:"center",flexWrap:"wrap"},safetyTitle:{fontSize:16,fontWeight:"800",color:"#3d4b82"},safetyCopy:{fontSize:12,color:"#7484ab",marginTop:5},pending:{fontSize:11,color:"#6565ad",padding:9,backgroundColor:"#d7dcf6",borderRadius:12},footer:{fontSize:10,color:"#93a0bc",textAlign:"center",marginTop:22}
});
