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
type Rota = {
  ordem: number; tempo_total_min: number; caminhada_m: number; baldeacoes: number;
  custo: { centavos: number | null; confirmado: boolean };
  seguranca: { status: string; exposicao: number | null };
  trechos: { modal: string | null; tipo: string; geometria: number[][]; linha?: string }[];
};
type ResultadoRotas = { resultado: { rotas: Rota[]; erro?: { mensagem: string } | null }; aviso: string };
const RAIO = 6371000;
const CENTRO = { lat: -23.55, lon: -46.63 };
const P = (x: number, y: number) => ({
  lat: CENTRO.lat + y / (RAIO * Math.PI / 180),
  lon: CENTRO.lon + x / ((RAIO * Math.PI / 180) * Math.cos(CENTRO.lat * Math.PI / 180)),
});
const PONTOS = [
  { nome: "Alfa (demonstração)", coords: P(0, -100) },
  { nome: "Beta (demonstração)", coords: P(2000, 100) },
  { nome: "Destino (demonstração)", coords: P(4000, 300) },
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
  const [resultadoRota, setResultadoRota] = useState<Rota | null>(null);
  const [buscandoRota, setBuscandoRota] = useState(false);
  const [erroRota, setErroRota] = useState("");
  const [indiceOrigem, setIndiceOrigem] = useState(0);
  const [indiceDestino, setIndiceDestino] = useState(2);

  const lat = posicao?.lat ?? -23.55;
  const lon = posicao?.lon ?? -46.63;
  const bbox = [lon-.045,lat-.045,lon+.045,lat+.045].join("%2C");
  const preview = `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik`;
  const geometria = resultadoRota?.trechos.flatMap(t => t.geometria || []) || [];
  const trajeto = geometria.filter((p,i,a) => i===0 || p[0]!==a[i-1][0] || p[1]!==a[i-1][1]);

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

  async function planejar() {
    setErroRota(""); setResultadoRota(null); setErro("");
    if (origem === "Localização atual" || posicao) {
      setErroRota("A rede piloto ainda não calcula rotas a partir da localização real. Escolha os pontos de demonstração abaixo.");
      return;
    }
    if (indiceOrigem === indiceDestino) {
      setErroRota("Selecione origem e destino diferentes."); return;
    }
    setBuscandoRota(true);
    try {
      const r = await fetch(API + "/rotas", {
        method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
          origem:PONTOS[indiceOrigem].coords, destino:PONTOS[indiceDestino].coords,
          partida:"2026-11-09T08:00:00", necessidades:{perfil_tarifario:"padrao"},
        }),
      });
      if (!r.ok) throw new Error("O módulo de rotas não respondeu.");
      const dados:ResultadoRotas = await r.json();
      if (dados.resultado.erro) throw new Error(dados.resultado.erro.mensagem);
      const candidatas = dados.resultado.rotas || [];
      const aderentes = candidatas.filter(rota => {
        const modais = rota.trechos.filter(t=>t.tipo==="transporte").map(t=>t.modal);
        if (modal==="ape") return modais.length === 0;
        if (modal==="onibus") return modais.includes("onibus");
        return modais.includes("metro") || modais.includes("trem");
      });
      if (!aderentes.length) {
        setErroRota("Nenhum trajeto desse modal disponível na rede de demonstração. Experimente outra opção de transporte.");
      } else {
        setResultadoRota(aderentes.reduce((a,b)=>a.tempo_total_min<=b.tempo_total_min?a:b));
        setRotaSolicitada(true);
      }
    } catch(e) {
      setErroRota(e instanceof Error ? e.message:"Não foi possível calcular.");
    } finally { setBuscandoRota(false); }
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
          <Text style={s.eyebrow}>CITIZEN TECH  ·  CIDADES INTELIGENTES</Text>
          <Text style={[s.heroTitle, mobile && s.heroTitleMobile]}>Sua cidade. Seu caminho.{"\n"}<Text style={s.heroAccent}>Mobilidade mais inteligente.</Text></Text>
          <Text style={s.heroCopy}>Explore conexões, compare possibilidades de deslocamento e encontre informações sobre transporte e direitos — tudo em uma única experiência.</Text>
        </View>
        {!mobile && <View style={s.heroArt}>
          <View style={s.techNetwork}>{btnIcone("git-network-outline","#6b60c9",68)}<View style={s.techBadge}>{btnIcone("sparkles-outline","#665bca",22)}<Text style={s.techText}>CITIZEN AI</Text></View></View>
          <Text style={s.heroArtSub}>Tecnologia conectando caminhos</Text>
        </View>}
      </View>

      <View style={s.planner}>
        <View style={s.plannerHeading}>{btnIcone("location-outline", "#605bc0", 23)}<Text style={s.plannerTitle}>Planejador de rotas</Text></View>
        <Text style={s.plannerCopy}>Simule um trajeto na rede piloto fictícia. A integração com dados reais ainda está em desenvolvimento.</Text>
        <View style={[s.planFields, mobile && s.planMobile]}>
          <View style={s.field}>
            <Pressable onPress={minhaLocalizacao} accessibilityLabel="Usar localização atual">
              {esperaLocal ? <ActivityIndicator color="#6263c4" /> : btnIcone("locate-outline")}
            </Pressable>
            <TextInput style={s.input} value={origem} onChangeText={t => {setOrigem(t);setPosicao(null);setRotaSolicitada(false);}} placeholder="De onde você vai sair?" placeholderTextColor="#8791b0" accessibilityLabel="Origem"/>
          </View>
          <Pressable onPress={() => {const o=origem;setOrigem(destino);setDestino(o);setPosicao(null);setRotaSolicitada(false);}} style={s.swap} accessibilityLabel="Inverter origem e destino">{btnIcone("swap-horizontal-outline")}</Pressable>
          <View style={s.field}>{btnIcone("location-outline")}<TextInput style={s.input} value={destino} onChangeText={t => {setDestino(t);setRotaSolicitada(false);}} placeholder="Para onde você quer ir?" placeholderTextColor="#8791b0" accessibilityLabel="Destino"/></View>
          <Pressable onPress={planejar} style={s.planButton}>{btnIcone("navigate-outline", "#fff")}<Text style={s.planButtonText}>{buscandoRota ? "Calculando..." : "Traçar no mapa"}</Text></Pressable>
        </View>
        {!!erro && <Text style={s.error}>{erro}</Text>}
        <View style={s.demoPoints}>
          <Text style={s.demoTitle}>PONTOS DO PILOTO (SIMULADOS)</Text>
          <View style={s.demoRow}>
            <Text style={s.demoLabel}>De:</Text>
            {PONTOS.map((p,i)=><Pressable key={"o"+i} onPress={()=>{setIndiceOrigem(i);setOrigem(p.nome);setPosicao(null);setResultadoRota(null);}} style={[s.demoChip,indiceOrigem===i&&s.demoChipOn]}><Text style={s.demoChipText}>{p.nome}</Text></Pressable>)}
          </View>
          <View style={s.demoRow}>
            <Text style={s.demoLabel}>Para:</Text>
            {PONTOS.map((p,i)=><Pressable key={"d"+i} onPress={()=>{setIndiceDestino(i);setDestino(p.nome);setResultadoRota(null);}} style={[s.demoChip,indiceDestino===i&&s.demoChipOn]}><Text style={s.demoChipText}>{p.nome}</Text></Pressable>)}
          </View>
        </View>
        <Text style={s.tip}>A localização atual apenas centraliza o mapa por enquanto. Cálculo real por endereço exige uma base de transporte validada.</Text>
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
          <View style={s.mapHeader}><Text style={s.mapTitle}>Mapa da viagem</Text><View style={s.mapPill}>{btnIcone("analytics-outline","#665abb",15)}<Text style={s.mapPillText}>Piloto simulado</Text></View></View>
          <MapaPreview url={preview} trajeto={trajeto}/>
          {buscandoRota && <ActivityIndicator color="#655beb" style={{marginVertical:12}}/>}
          {!!erroRota && <Text style={s.error}>{erroRota}</Text>}
          {resultadoRota ? <View style={s.routeSummary}>
            <Text style={s.routeTitle}>Trajeto {resultadoRota.ordem} · {modal==="ape"?"Caminhada":modal==="onibus"?"Ônibus":"Trem / Metrô"}</Text>
            <View style={s.routeStats}>
              <View style={s.routeStat}><Text style={s.routeStatLabel}>TEMPO ESTIMADO</Text><Text style={s.routeStatValue}>{resultadoRota.tempo_total_min} min</Text></View>
              <View style={s.routeStat}><Text style={s.routeStatLabel}>TARIFA FICTÍCIA</Text><Text style={s.routeStatValue}>{resultadoRota.custo?.centavos==null?"Não confirmada":`R$ ${(resultadoRota.custo.centavos/100).toFixed(2).replace(".",",")}`}</Text></View>
              <View style={s.routeStat}><Text style={s.routeStatLabel}>SEGURANÇA</Text><Text style={s.routeStatValue}>Não verificada</Text></View>
            </View>
            <Text style={s.routeNote}>Traçado baseado na geometria da rede de testes, não em operação real. Caminhada: {resultadoRota.caminhada_m} m. Baldeações: {resultadoRota.baldeacoes}. Nenhum índice de segurança disponível.</Text>
          </View> : <Text style={s.mapBottomSub}>Selecione os pontos do piloto e um modal; o percurso será desenhado aqui sem abrir outro site.</Text>}
        </View>

      <View style={s.safety}>{btnIcone("shield-checkmark-outline","#6863b6",31)}<View style={{flex:1}}><Text style={s.safetyTitle}>Indicadores de segurança por região</Text><Text style={s.safetyText}>Em desenvolvimento: futuramente serão apresentados dados agregados e suas fontes, sem promessas de trajetos seguros.</Text></View><View style={s.status}><Text style={s.statusText}>Em desenvolvimento</Text></View></View>
      <Text style={s.footer}>Citizen Tech Mobilidade Urbana · Protótipo FIAP 2026. Dados de rotas reais são consultados em serviço externo.</Text>
    </View>
  </ScrollView>;
}

const s=StyleSheet.create({
  techNetwork:{width:170,height:130,borderRadius:30,alignItems:"center",justifyContent:"center",borderWidth:1,borderColor:"#bdc5f5",backgroundColor:"#e7eaff"},techBadge:{position:"absolute",right:-23,bottom:0,backgroundColor:"#fff",padding:12,borderRadius:14,alignItems:"center",flexDirection:"row",gap:7},techText:{color:"#5653ae",fontSize:12,fontWeight:"800"},
  demoPoints:{marginTop:14,gap:8},demoTitle:{fontSize:11,fontWeight:"800",color:"#6670b3",letterSpacing:1},demoRow:{flexDirection:"row",flexWrap:"wrap",alignItems:"center",gap:6},demoLabel:{color:"#627197",fontWeight:"700",fontSize:12,minWidth:28},demoChip:{borderRadius:8,paddingVertical:6,paddingHorizontal:9,backgroundColor:"#eef1fa"},demoChipOn:{backgroundColor:"#d8dcff",borderWidth:1,borderColor:"#766dd0"},demoChipText:{fontSize:11,color:"#4d5a95"},
  routeSummary:{marginTop:12,backgroundColor:"#f6f6ff",padding:13,borderRadius:12},routeTitle:{fontSize:14,color:"#40508a",fontWeight:"800"},routeStats:{flexDirection:"row",flexWrap:"wrap",marginTop:12,gap:9},routeStat:{flex:1,minWidth:100,backgroundColor:"#fff",padding:10,borderRadius:9},routeStatLabel:{fontSize:9,color:"#7c86a9",fontWeight:"700"},routeStatValue:{fontSize:17,color:"#393d87",fontWeight:"800",marginTop:5},routeNote:{color:"#8b91a9",fontSize:11,lineHeight:18,marginTop:11},

  root:{flex:1,backgroundColor:"#ecf0fe"},page:{alignItems:"center",paddingHorizontal:18,paddingVertical:22},wrap:{width:"100%",maxWidth:1320},
  header:{flexDirection:"row",alignItems:"center",gap:13,marginBottom:25},logo:{height:43,width:43,backgroundColor:"#6261ba",alignItems:"center",justifyContent:"center",borderRadius:12},brand:{fontSize:21,fontWeight:"800",color:"#263d84"},brandSub:{color:"#6475ad",fontSize:14},headerBadge:{marginLeft:"auto",borderRadius:12,padding:10,backgroundColor:"#e0e6fa"},headerBadgeText:{color:"#6572aa",fontSize:11,fontWeight:"700"},
  hero:{padding:26,backgroundColor:"#dee6ff",borderRadius:14,flexDirection:"row",alignItems:"center",minHeight:205},heroMobile:{padding:20},heroText:{flex:1},eyebrow:{fontSize:11,letterSpacing:2,fontWeight:"800",color:"#626cb4",marginBottom:11},heroTitle:{color:"#263c76",fontSize:36,lineHeight:45,fontWeight:"800"},heroTitleMobile:{fontSize:27,lineHeight:36},heroAccent:{color:"#7567cc"},heroCopy:{color:"#6979a4",fontSize:15,lineHeight:23,marginTop:10,maxWidth:630},heroArt:{width:260,alignItems:"center"},heroArtSub:{color:"#6d78a8",fontSize:12,fontWeight:"700",marginTop:8},
  planner:{backgroundColor:"#fff",borderRadius:17,padding:21,marginTop:17},plannerHeading:{flexDirection:"row",alignItems:"center",gap:10},plannerTitle:{fontSize:21,color:"#273965",fontWeight:"800"},plannerCopy:{fontSize:13,color:"#7887a8",marginTop:7,marginBottom:14},
  planFields:{flexDirection:"row",alignItems:"center",gap:10},planMobile:{flexWrap:"wrap"},field:{flex:1,minWidth:185,borderWidth:1,borderColor:"#dce2f4",backgroundColor:"#f9faff",borderRadius:11,minHeight:51,flexDirection:"row",alignItems:"center",paddingHorizontal:13,gap:9},input:{flex:1,fontSize:14,color:"#354874",paddingVertical:11,minWidth:50},swap:{height:45,width:45,alignItems:"center",justifyContent:"center",backgroundColor:"#eff2ff",borderRadius:10},planButton:{backgroundColor:"#515fb4",borderRadius:11,minHeight:51,flexDirection:"row",alignItems:"center",justifyContent:"center",paddingHorizontal:18,gap:9},planButtonText:{color:"#fff",fontSize:14,fontWeight:"800"},tip:{color:"#8d97b1",fontSize:11,marginTop:10},error:{color:"#b23e55",marginTop:10,fontSize:13},
  transportRow:{flexDirection:"row",gap:15,marginTop:17},transportMobile:{flexWrap:"wrap"},transportCard:{flex:1,minWidth:185,height:170,overflow:"hidden",borderRadius:13,borderWidth:2,borderColor:"transparent"},transportActive:{borderColor:"#6453c6"},transportPhoto:{height:"100%",justifyContent:"flex-end"},transportImage:{borderRadius:10},transportShade:{position:"absolute",left:0,right:0,bottom:0,height:78,backgroundColor:"rgba(26,39,85,.72)"},transportOverlay:{flexDirection:"row",alignItems:"center",gap:12,padding:16},transportLabel:{flex:1,color:"#fff",fontWeight:"800",fontSize:19},transportArrow:{width:30,height:30,backgroundColor:"rgba(255,255,255,.2)",borderRadius:16,alignItems:"center",justifyContent:"center"},
  contentRow:{flexDirection:"row",gap:17,marginTop:20,alignItems:"stretch"},contentMobile:{flexWrap:"wrap"},chatPanel:{flex:1,minWidth:280,backgroundColor:"#f9f8ff",borderWidth:1,borderColor:"#e0defc",borderRadius:32,padding:23},chatHeader:{flexDirection:"row",alignItems:"center",gap:13},chatAvatar:{width:51,height:51,borderRadius:25,backgroundColor:"#e5e4ff",alignItems:"center",justifyContent:"center"},chatTitle:{fontSize:19,fontWeight:"800",color:"#293866"},chatIntro:{color:"#7380a3",fontSize:13,marginTop:5,lineHeight:19},suggestions:{flexDirection:"row",flexWrap:"wrap",gap:8,marginTop:19},chip:{backgroundColor:"#e9ebfc",borderWidth:1,borderColor:"#dce0fa",borderRadius:25,paddingVertical:8,paddingHorizontal:13},chipText:{color:"#5969a7",fontSize:12,fontWeight:"600"},messages:{maxHeight:210,marginTop:12,gap:9},emptyChat:{color:"#8a94b4",fontSize:13,lineHeight:20,marginVertical:9},bubble:{padding:12,borderRadius:17,maxWidth:"95%"},bubbleUser:{alignSelf:"flex-end",backgroundColor:"#6566bb"},bubbleAi:{alignSelf:"flex-start",backgroundColor:"#e9ecfb"},bubbleText:{color:"#4c5c8e",fontSize:13,lineHeight:19},bubbleUserText:{color:"#fff"},source:{fontSize:11,color:"#6173a7",marginTop:6},chatInputWrap:{borderWidth:1,borderColor:"#c9d1f0",borderRadius:27,backgroundColor:"#fff",minHeight:50,flexDirection:"row",alignItems:"center",paddingLeft:15,paddingRight:5,marginTop:12},chatInput:{flex:1,fontSize:14,color:"#3b4a83",paddingVertical:10},send:{backgroundColor:"#7772d3",width:40,height:40,borderRadius:21,alignItems:"center",justifyContent:"center"},chatDisclaimer:{fontSize:10,color:"#98a0bb",marginTop:10,lineHeight:15},
  mapPanel:{flex:1.12,minWidth:280,backgroundColor:"#fff",borderRadius:17,padding:14},mapHeader:{flexDirection:"row",alignItems:"center",justifyContent:"space-between",gap:10,flexWrap:"wrap",marginBottom:11},mapTitle:{fontSize:18,fontWeight:"800",color:"#364879"},mapPill:{flexDirection:"row",alignItems:"center",gap:5,backgroundColor:"#edeaff",borderRadius:14,padding:8},mapPillText:{fontSize:11,color:"#655db2",fontWeight:"700"},mapBottom:{flexDirection:"row",alignItems:"center",gap:12,padding:13},mapBottomTitle:{color:"#364879",fontSize:15,fontWeight:"800"},mapBottomSub:{color:"#8793b0",fontSize:11,marginTop:5,lineHeight:17},mapButton:{backgroundColor:"#625fc2",width:40,height:40,borderRadius:11,alignItems:"center",justifyContent:"center"},
  safety:{marginTop:19,borderRadius:16,backgroundColor:"#e0e6fc",padding:18,flexDirection:"row",alignItems:"center",gap:13,flexWrap:"wrap"},safetyTitle:{fontWeight:"800",color:"#384575",fontSize:17},safetyText:{color:"#7481a7",fontSize:12,lineHeight:19,marginTop:5},status:{backgroundColor:"#d5d9f8",borderRadius:15,padding:9},statusText:{color:"#676bb5",fontSize:11,fontWeight:"700"},footer:{fontSize:11,color:"#939db8",textAlign:"center",marginTop:22}
});
