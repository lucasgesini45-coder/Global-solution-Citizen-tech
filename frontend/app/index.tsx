import React, { useState } from "react";
import {
  ActivityIndicator, ImageBackground, Linking, Pressable, ScrollView,
  StyleSheet, Text, TextInput, View, useWindowDimensions,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import * as Location from "expo-location";
import MapaPreview from "../components/MapaPreview";

type Icone = React.ComponentProps<typeof Ionicons>["name"];
type Modal = "ferroviario" | "onibus" | "ape";
type Consulta = { status: string; resposta: string; fontes: { referencia: string; data_verificacao: string }[]; relacionados: string[] };
const API = (process.env.EXPO_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const MODAIS: { id: Modal; nome: string; icone: Icone; foto: string }[] = [
  { id: "ferroviario", nome: "Trem e Metrô", icone: "train-outline", foto: "https://images.unsplash.com/photo-1519608487953-e999c86e7455?w=1100&q=85" },
  { id: "onibus", nome: "Ônibus", icone: "bus-outline", foto: "https://images.unsplash.com/photo-1570125909232-eb263c188f7e?w=1100&q=85" },
  { id: "ape", nome: "A pé", icone: "walk-outline", foto: "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?w=1100&q=85" },
];
const SUGESTOES = [
  "Como emitir cartão?", "Quais são meus direitos?",
  "Como pedir gratuidade?", "Como funciona a integração?",
];

function btnIcone(nome: Icone, cor = "#5364b5", tamanho = 20) {
  return <Ionicons name={nome} color={cor} size={tamanho} />;
}

export default function Home() {
  const { width } = useWindowDimensions();
  const mobile = width < 750;
  const [modal, setModal] = useState<Modal>("ferroviario");
  const [origem, setOrigem] = useState("");
  const [destino, setDestino] = useState("");
  const [posicao, setPosicao] = useState<{ lat: number; lon: number } | null>(null);
  const [esperaLocal, setEsperaLocal] = useState(false);
  const [pergunta, setPergunta] = useState("");
  const [chat, setChat] = useState<{ autor: "usuario" | "agente"; texto: string; fontes?: string[] }[]>([]);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState("");
  const [rotaSolicitada, setRotaSolicitada] = useState(false);

  const mapKey = process.env.EXPO_PUBLIC_GOOGLE_MAPS_EMBED_KEY;
  const lat = posicao?.lat ?? -23.5505;
  const lon = posicao?.lon ?? -46.6333;
  const bbox = [lon - .035, lat - .035, lon + .035, lat + .035].join("%2C");
  const preview = `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik${posicao ? `&marker=${lat}%2C${lon}` : ""}`;
  const origemMap = posicao && origem === "Localização atual" ? `${lat},${lon}` : origem.trim();
  const mode = modal === "ape" ? "walking" : "transit";
  const embed = rotaSolicitada && mapKey && origemMap && destino.trim()
    ? `https://www.google.com/maps/embed/v1/directions?key=${encodeURIComponent(mapKey)}&origin=${encodeURIComponent(origemMap)}&destination=${encodeURIComponent(destino.trim())}&mode=${mode}`
    : preview;

  const linkRota = () => {
    const p = new URLSearchParams({ api: "1", origin: origemMap, destination: destino.trim(), travelmode: mode });
    if (modal === "onibus") p.set("transit_mode", "bus");
    if (modal === "ferroviario") p.set("transit_mode", "rail");
    return `https://www.google.com/maps/dir/?${p.toString()}`;
  };

  async function minhaLocalizacao() {
    setEsperaLocal(true); setErro("");
    try {
      const perm = await Location.requestForegroundPermissionsAsync();
      if (perm.status !== "granted") {
        setErro("Localização não autorizada. Você pode digitar sua origem."); return;
      }
      const atual = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
      setPosicao({ lat: atual.coords.latitude, lon: atual.coords.longitude });
      setOrigem("Localização atual"); setRotaSolicitada(false);
    } catch { setErro("Não foi possível obter sua localização."); }
    finally { setEsperaLocal(false); }
  }

  function planejar() {
    if (!origemMap || !destino.trim()) { setErro("Informe a origem e o destino para planejar a viagem."); return; }
    setErro(""); setRotaSolicitada(true);
    // O roteamento real e o ETA são realizados pelo Google Maps.
    Linking.openURL(linkRota()).catch(() => setErro("Não foi possível abrir o serviço de rotas."));
  }

  async function perguntar(texto = pergunta) {
    if (!texto.trim() || carregando) return;
    const mensagem = texto.trim();
    setPergunta(""); setCarregando(true);
    setChat(v => [...v, { autor: "usuario", texto: mensagem }]);
    try {
      const r = await fetch(API + "/consultar", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pergunta: mensagem, modelo: "B" }),
      });
      if (!r.ok) throw new Error("Serviço de consultas indisponível.");
      const dados: Consulta = await r.json();
      setChat(v => [...v, {
        autor: "agente", texto: dados.resposta,
        fontes: (dados.fontes || []).map(f => `${f.referencia} · ${f.data_verificacao}`),
      }]);
    } catch {
      setChat(v => [...v, { autor: "agente", texto: "Não consegui conectar à base de orientações. Verifique se a API está ligada." }]);
    } finally { setCarregando(false); }
  }

  return <ScrollView style={s.root} contentContainerStyle={s.page}>
    <View style={s.wrap}>
      <View style={s.header}>
        <View style={s.logo}>{btnIcone("navigate", "#fff", 23)}</View>
        <View><Text style={s.brand}>Citizen Tech</Text><Text style={s.brandSub}>Mobilidade Urbana</Text></View>
        <View style={s.headerBadge}><Text style={s.headerBadgeText}>FIAP · Global Solution 2026</Text></View>
      </View>

      <View style={[s.hero, mobile && s.heroMobile]}>
        <View style={s.heroText}>
          <Text style={s.eyebrow}>SUA MOBILIDADE NA CIDADE</Text>
          <Text style={[s.heroTitle, mobile && s.heroTitleMobile]}>Planeje, viaje e se{"\n"}<Text style={s.heroAccent}>informe com inteligência.</Text></Text>
          <Text style={s.heroCopy}>Um lugar para encontrar trajetos e orientações confiáveis sobre transporte público e seus direitos.</Text>
        </View>
        {!mobile && <View style={s.heroArt}>{btnIcone("train-outline", "#5366bb", 96)}<Text style={s.heroArtSub}>A cidade ao seu alcance</Text></View>}
      </View>

      <View style={s.planner}>
        <View style={s.plannerHeading}>{btnIcone("location-outline", "#605bc0", 23)}<Text style={s.plannerTitle}>Planejador de rotas</Text></View>
        <Text style={s.plannerCopy}>Escolha um destino e compare as opções de deslocamento.</Text>
        <View style={[s.planFields, mobile && s.planMobile]}>
          <View style={s.field}>
            <Pressable onPress={minhaLocalizacao} accessibilityLabel="Usar localização atual">
              {esperaLocal ? <ActivityIndicator color="#6263c4" /> : btnIcone("locate-outline")}
            </Pressable>
            <TextInput style={s.input} value={origem} onChangeText={t => {setOrigem(t);setPosicao(null);setRotaSolicitada(false);}} placeholder="De onde você vai sair?" placeholderTextColor="#8791b0" accessibilityLabel="Origem"/>
          </View>
          <Pressable onPress={() => {const o=origem;setOrigem(destino);setDestino(o);setPosicao(null);setRotaSolicitada(false);}} style={s.swap} accessibilityLabel="Inverter origem e destino">{btnIcone("swap-horizontal-outline")}</Pressable>
          <View style={s.field}>{btnIcone("location-outline")}<TextInput style={s.input} value={destino} onChangeText={t => {setDestino(t);setRotaSolicitada(false);}} placeholder="Para onde você quer ir?" placeholderTextColor="#8791b0" accessibilityLabel="Destino"/></View>
          <Pressable onPress={planejar} style={s.planButton}>{btnIcone("navigate-outline", "#fff")}<Text style={s.planButtonText}>Planejar rota</Text></Pressable>
        </View>
        {!!erro && <Text style={s.error}>{erro}</Text>}
        <Text style={s.tip}>Toque no ícone de localização para usar sua posição atual, com sua autorização.</Text>
      </View>

      <View style={[s.transportRow, mobile && s.transportMobile]}>{MODAIS.map(t =>
        <Pressable key={t.id} style={[s.transportCard, modal === t.id && s.transportActive]} onPress={() => {setModal(t.id);setRotaSolicitada(false);}} accessibilityRole="button" accessibilityState={{selected:modal===t.id}}>
          <ImageBackground source={{uri:t.foto}} style={s.transportPhoto} imageStyle={s.transportImage}>
            <View style={s.transportShade} />
            <View style={s.transportOverlay}>{btnIcone(t.icone, "#fff", 26)}<Text style={s.transportLabel}>{t.nome}</Text><View style={s.transportArrow}>{btnIcone("chevron-forward", "#fff", 21)}</View></View>
          </ImageBackground>
        </Pressable>
      )}</View>

      <View style={[s.contentRow, mobile && s.contentMobile]}>
        <View style={s.chatPanel}>
          <View style={s.chatHeader}><View style={s.chatAvatar}>{btnIcone("sparkles-outline", "#625acf", 26)}</View><View style={{flex:1}}><Text style={s.chatTitle}>Pergunte ao nosso Agente de IA</Text><Text style={s.chatIntro}>Dúvidas sobre cartões, benefícios, direitos e transporte.</Text></View></View>
          <View style={s.suggestions}>{SUGESTOES.map(x => <Pressable key={x} onPress={() => perguntar(x)} style={s.chip}><Text style={s.chipText}>{x}</Text></Pressable>)}</View>
          <View style={s.messages}>{chat.length === 0 ? <Text style={s.emptyChat}>Escolha uma sugestão ou escreva sua dúvida para começar.</Text> : chat.map((msg,i) => <View key={i} style={[s.bubble,msg.autor==="usuario"?s.bubbleUser:s.bubbleAi]}><Text style={[s.bubbleText,msg.autor==="usuario"&&s.bubbleUserText]}>{msg.texto}</Text>{msg.fontes?.map((f,j)=><Text selectable key={j} style={s.source}>{f}</Text>)}</View>)}</View>
          <View style={s.chatInputWrap}><TextInput style={s.chatInput} value={pergunta} onChangeText={setPergunta} placeholder="Digite sua pergunta..." placeholderTextColor="#8c96b6" returnKeyType="send" onSubmitEditing={() => perguntar()} accessibilityLabel="Mensagem para assistente"/><Pressable onPress={() => perguntar()} style={s.send} accessibilityLabel="Enviar pergunta">{carregando?<ActivityIndicator color="#fff"/>:btnIcone("send-outline","#fff",21)}</Pressable></View>
          <Text style={s.chatDisclaimer}>Assistente acadêmico: responde somente com orientações verificadas na base.</Text>
        </View>
        <View style={s.mapPanel}>
          <View style={s.mapHeader}><Text style={s.mapTitle}>Mapa do trajeto</Text><View style={s.mapPill}>{btnIcone("flash-outline","#665abb",15)}<Text style={s.mapPillText}>Trajeto mais rápido: consultar</Text></View></View>
          <MapaPreview url={embed}/>
          <View style={s.mapBottom}><View style={{flex:1}}><Text style={s.mapBottomTitle}>{rotaSolicitada ? "Trajeto solicitado" : "Selecione origem e destino"}</Text><Text style={s.mapBottomSub}>{mapKey && rotaSolicitada ? "Mapa de direções incorporado" : "Prévia da região: tempo e melhor percurso disponíveis no Google Maps"}</Text></View><Pressable style={s.mapButton} onPress={() => origemMap && destino.trim()?Linking.openURL(linkRota()):setErro("Informe origem e destino no planejador.")}>{btnIcone("open-outline","#fff",19)}</Pressable></View>
        </View>
      </View>

      <View style={s.safety}>{btnIcone("shield-checkmark-outline","#6863b6",31)}<View style={{flex:1}}><Text style={s.safetyTitle}>Indicadores de segurança por região</Text><Text style={s.safetyText}>Em desenvolvimento: futuramente serão apresentados dados agregados e suas fontes, sem promessas de trajetos seguros.</Text></View><View style={s.status}><Text style={s.statusText}>Em desenvolvimento</Text></View></View>
      <Text style={s.footer}>Citizen Tech Mobilidade Urbana · Protótipo FIAP 2026. Dados de rotas reais são consultados em serviço externo.</Text>
    </View>
  </ScrollView>;
}

const s=StyleSheet.create({
  root:{flex:1,backgroundColor:"#ecf0fe"},page:{alignItems:"center",paddingHorizontal:18,paddingVertical:22},wrap:{width:"100%",maxWidth:1320},
  header:{flexDirection:"row",alignItems:"center",gap:13,marginBottom:25},logo:{height:43,width:43,backgroundColor:"#6261ba",alignItems:"center",justifyContent:"center",borderRadius:12},brand:{fontSize:21,fontWeight:"800",color:"#263d84"},brandSub:{color:"#6475ad",fontSize:14},headerBadge:{marginLeft:"auto",borderRadius:12,padding:10,backgroundColor:"#e0e6fa"},headerBadgeText:{color:"#6572aa",fontSize:11,fontWeight:"700"},
  hero:{padding:26,backgroundColor:"#dee6ff",borderRadius:18,flexDirection:"row",alignItems:"center",minHeight:205},heroMobile:{padding:20},heroText:{flex:1},eyebrow:{fontSize:11,letterSpacing:2,fontWeight:"800",color:"#626cb4",marginBottom:11},heroTitle:{color:"#263c76",fontSize:36,lineHeight:45,fontWeight:"800"},heroTitleMobile:{fontSize:27,lineHeight:36},heroAccent:{color:"#7567cc"},heroCopy:{color:"#6979a4",fontSize:15,lineHeight:23,marginTop:10,maxWidth:630},heroArt:{width:260,alignItems:"center"},heroArtSub:{color:"#6d78a8",fontSize:12,fontWeight:"700",marginTop:8},
  planner:{backgroundColor:"#fff",borderRadius:17,padding:21,marginTop:17},plannerHeading:{flexDirection:"row",alignItems:"center",gap:10},plannerTitle:{fontSize:21,color:"#273965",fontWeight:"800"},plannerCopy:{fontSize:13,color:"#7887a8",marginTop:7,marginBottom:14},
  planFields:{flexDirection:"row",alignItems:"center",gap:10},planMobile:{flexWrap:"wrap"},field:{flex:1,minWidth:185,borderWidth:1,borderColor:"#dce2f4",backgroundColor:"#f9faff",borderRadius:11,minHeight:51,flexDirection:"row",alignItems:"center",paddingHorizontal:13,gap:9},input:{flex:1,fontSize:14,color:"#354874",paddingVertical:11,minWidth:50},swap:{height:45,width:45,alignItems:"center",justifyContent:"center",backgroundColor:"#eff2ff",borderRadius:10},planButton:{backgroundColor:"#515fb4",borderRadius:11,minHeight:51,flexDirection:"row",alignItems:"center",justifyContent:"center",paddingHorizontal:18,gap:9},planButtonText:{color:"#fff",fontSize:14,fontWeight:"800"},tip:{color:"#8d97b1",fontSize:11,marginTop:10},error:{color:"#b23e55",marginTop:10,fontSize:13},
  transportRow:{flexDirection:"row",gap:15,marginTop:17},transportMobile:{flexWrap:"wrap"},transportCard:{flex:1,minWidth:185,height:170,overflow:"hidden",borderRadius:13,borderWidth:2,borderColor:"transparent"},transportActive:{borderColor:"#6453c6"},transportPhoto:{height:"100%",justifyContent:"flex-end"},transportImage:{borderRadius:10},transportShade:{position:"absolute",left:0,right:0,bottom:0,height:78,backgroundColor:"rgba(26,39,85,.72)"},transportOverlay:{flexDirection:"row",alignItems:"center",gap:12,padding:16},transportLabel:{flex:1,color:"#fff",fontWeight:"800",fontSize:19},transportArrow:{width:30,height:30,backgroundColor:"rgba(255,255,255,.2)",borderRadius:16,alignItems:"center",justifyContent:"center"},
  contentRow:{flexDirection:"row",gap:17,marginTop:20,alignItems:"stretch"},contentMobile:{flexWrap:"wrap"},chatPanel:{flex:1,minWidth:280,backgroundColor:"#f9f8ff",borderWidth:1,borderColor:"#e0defc",borderRadius:32,padding:23},chatHeader:{flexDirection:"row",alignItems:"center",gap:13},chatAvatar:{width:51,height:51,borderRadius:25,backgroundColor:"#e5e4ff",alignItems:"center",justifyContent:"center"},chatTitle:{fontSize:19,fontWeight:"800",color:"#293866"},chatIntro:{color:"#7380a3",fontSize:13,marginTop:5,lineHeight:19},suggestions:{flexDirection:"row",flexWrap:"wrap",gap:8,marginTop:19},chip:{backgroundColor:"#e9ebfc",borderWidth:1,borderColor:"#dce0fa",borderRadius:25,paddingVertical:8,paddingHorizontal:13},chipText:{color:"#5969a7",fontSize:12,fontWeight:"600"},messages:{maxHeight:210,marginTop:12,gap:9},emptyChat:{color:"#8a94b4",fontSize:13,lineHeight:20,marginVertical:9},bubble:{padding:12,borderRadius:17,maxWidth:"95%"},bubbleUser:{alignSelf:"flex-end",backgroundColor:"#6566bb"},bubbleAi:{alignSelf:"flex-start",backgroundColor:"#e9ecfb"},bubbleText:{color:"#4c5c8e",fontSize:13,lineHeight:19},bubbleUserText:{color:"#fff"},source:{fontSize:11,color:"#6173a7",marginTop:6},chatInputWrap:{borderWidth:1,borderColor:"#c9d1f0",borderRadius:27,backgroundColor:"#fff",minHeight:50,flexDirection:"row",alignItems:"center",paddingLeft:15,paddingRight:5,marginTop:12},chatInput:{flex:1,fontSize:14,color:"#3b4a83",paddingVertical:10},send:{backgroundColor:"#7772d3",width:40,height:40,borderRadius:21,alignItems:"center",justifyContent:"center"},chatDisclaimer:{fontSize:10,color:"#98a0bb",marginTop:10,lineHeight:15},
  mapPanel:{flex:1.12,minWidth:280,backgroundColor:"#fff",borderRadius:17,padding:14},mapHeader:{flexDirection:"row",alignItems:"center",justifyContent:"space-between",gap:10,flexWrap:"wrap",marginBottom:11},mapTitle:{fontSize:18,fontWeight:"800",color:"#364879"},mapPill:{flexDirection:"row",alignItems:"center",gap:5,backgroundColor:"#edeaff",borderRadius:14,padding:8},mapPillText:{fontSize:11,color:"#655db2",fontWeight:"700"},mapBottom:{flexDirection:"row",alignItems:"center",gap:12,padding:13},mapBottomTitle:{color:"#364879",fontSize:15,fontWeight:"800"},mapBottomSub:{color:"#8793b0",fontSize:11,marginTop:5,lineHeight:17},mapButton:{backgroundColor:"#625fc2",width:40,height:40,borderRadius:11,alignItems:"center",justifyContent:"center"},
  safety:{marginTop:19,borderRadius:16,backgroundColor:"#e0e6fc",padding:18,flexDirection:"row",alignItems:"center",gap:13,flexWrap:"wrap"},safetyTitle:{fontWeight:"800",color:"#384575",fontSize:17},safetyText:{color:"#7481a7",fontSize:12,lineHeight:19,marginTop:5},status:{backgroundColor:"#d5d9f8",borderRadius:15,padding:9},statusText:{color:"#676bb5",fontSize:11,fontWeight:"700"},footer:{fontSize:11,color:"#939db8",textAlign:"center",marginTop:22}
});
