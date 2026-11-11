import React, { useState } from "react";
import {
  ActivityIndicator, ImageBackground, Linking, Pressable, ScrollView,
  StyleSheet, Text, TextInput, View, useWindowDimensions,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import * as Location from "expo-location";
import { useRouter } from "expo-router";

type Modal = "ferroviario" | "onibus" | "ape";
type Icone = React.ComponentProps<typeof Ionicons>["name"];
type Transporte = {
  id: Modal; titulo: string; legenda: string; icon: Icone;
  foto: string; fonte: string; mapa: string; mapaNome: string;
};

const transportes: Transporte[] = [
  {
    id: "ferroviario", titulo: "Trem e Metrô",
    legenda: "Estações, conexões e linhas metropolitanas",
    icon: "train-outline",
    foto: "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/S%C3%A3o_Paulo_Metro%2C_Line_blue%2C_Brazil.jpg/800px-S%C3%A3o_Paulo_Metro%2C_Line_blue%2C_Brazil.jpg",
    fonte: "Foto: Wikimedia Commons",
    mapa: "https://www.metro.sp.gov.br/sua-viagem/mapa-da-rede/",
    mapaNome: "Consultar mapa oficial da rede ferroviária",
  },
  {
    id: "onibus", titulo: "Ônibus",
    legenda: "Linhas, itinerários e pontos de embarque",
    icon: "bus-outline",
    foto: "https://www.sptrans.com.br/media/3672/imagem-sptrans.jpg",
    fonte: "Foto: SPTrans",
    mapa: "https://www.sptrans.com.br/",
    mapaNome: "Consultar linhas e itinerários na SPTrans",
  },
  {
    id: "ape", titulo: "A pé",
    legenda: "Percursos de caminhada pela cidade",
    icon: "walk-outline",
    foto: "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Cal%C3%A7ad%C3%A3o_da_Av_Paulista_-_Sao_Paulo_SP_-_panoramio.jpg/800px-Cal%C3%A7ad%C3%A3o_da_Av_Paulista_-_Sao_Paulo_SP_-_panoramio.jpg",
    fonte: "Foto: Wikimedia Commons",
    mapa: "https://www.openstreetmap.org/",
    mapaNome: "Explorar o mapa de ruas e calçadas",
  },
];

export default function Mobilidade() {
  const router = useRouter();
  const { width } = useWindowDimensions();
  const compacto = width < 700;
  const [modal, setModal] = useState<Modal | null>(null);
  const [origem, setOrigem] = useState("");
  const [destino, setDestino] = useState("");
  const [coords, setCoords] = useState<{ latitude: number; longitude: number } | null>(null);
  const [buscando, setBuscando] = useState(false);
  const [erro, setErro] = useState("");

  const atual = transportes.find(t => t.id === modal);
  const [lat, lon] = coords ? [coords.latitude, coords.longitude] : [-23.5505, -46.6333];
  // Este quadro exibe a região e o marcador de origem; a rota real abre no Google Maps.
  const zoom = 0.035;
  const bbox = [lon - zoom, lat - zoom, lon + zoom, lat + zoom].join("%2C");
  const marcador = coords ? `&marker=${lat}%2C${lon}` : "";
  const mapaPreview = `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik${marcador}`;

  function escolher(id: Modal) {
    setModal(id);
    setErro("");
  }

  async function usarLocalizacao() {
    setBuscando(true);
    setErro("");
    try {
      const permissao = await Location.requestForegroundPermissionsAsync();
      if (permissao.status !== "granted") {
        setErro("Permissão de localização não concedida. Você pode informar a origem manualmente.");
        return;
      }
      const local = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
      setCoords({ latitude: local.coords.latitude, longitude: local.coords.longitude });
      setOrigem("Localização atual");
    } catch {
      setErro("Não foi possível obter sua localização. Digite a origem manualmente.");
    } finally {
      setBuscando(false);
    }
  }

  function abrirRotas() {
    if (!destino.trim()) {
      setErro("Informe um destino para traçar o percurso.");
      return;
    }
    if (!origem.trim() && !coords) {
      setErro("Informe a origem ou escolha usar a localização atual.");
      return;
    }
    setErro("");
    const params = new URLSearchParams();
    params.set("api", "1");
    params.set("origin", origem === "Localização atual" && coords
      ? `${coords.latitude},${coords.longitude}` : origem.trim());
    params.set("destination", destino.trim());
    params.set("travelmode", modal === "ape" ? "walking" : "transit");
    if (modal === "onibus") params.set("transit_mode", "bus");
    if (modal === "ferroviario") params.set("transit_mode", "rail");
    Linking.openURL("https://www.google.com/maps/dir/?" + params.toString()).catch(
      () => setErro("Não foi possível abrir o mapa de rotas.")
    );
  }

  return (
    <ScrollView style={s.background} contentContainerStyle={s.page}>
      <View style={s.container}>
        <Pressable onPress={() => router.back()} style={s.voltar}>
          <Ionicons name="arrow-back" size={19} color="#5666a4" />
          <Text style={s.voltarTexto}>Voltar ao início</Text>
        </Pressable>
        <View style={s.topo}>
          <Text style={s.supertitulo}>CITIZEN MOBILIDADE</Text>
          <Text style={[s.titulo, compacto && s.tituloMobile]}>Como você deseja <Text style={s.destaque}>se deslocar?</Text></Text>
          <Text style={s.subtitulo}>Escolha seu meio de transporte para consultar rotas e explorar os mapas da cidade.</Text>
        </View>
        <View style={s.cards}>
          {transportes.map(t => (
            <Pressable
              key={t.id}
              accessibilityRole="button"
              accessibilityLabel={`Selecionar ${t.titulo}`}
              onPress={() => escolher(t.id)}
              style={[s.card, compacto && s.cardMobile, modal === t.id && s.cardAtivo]}
            >
              <ImageBackground source={{ uri: t.foto }} imageStyle={s.foto} style={s.imagem}>
                <View style={s.iconeFoto}><Ionicons name={t.icon} color="#fff" size={22} /></View>
              </ImageBackground>
              <View style={s.cardCorpo}>
                <Text style={s.cardTitulo}>{t.titulo}</Text>
                <Text style={s.cardLegenda}>{t.legenda}</Text>
                <View style={s.cardRodape}><Text style={s.escolher}>Selecionar transporte</Text><Ionicons name="arrow-forward" size={17} color="#6864c8" /></View>
              </View>
            </Pressable>
          ))}
        </View>

        {atual ? <View style={s.painel}>
          <View style={s.painelCabecalho}>
            <View style={s.painelIcone}><Ionicons name={atual.icon} size={23} color="#655fbf" /></View>
            <View style={{ flex: 1 }}>
              <Text style={s.painelTitulo}>Planejar trajeto de {atual.titulo.toLowerCase()}</Text>
              <Text style={s.painelSub}>Escolha onde começa e para onde vai.</Text>
            </View>
          </View>
          <View style={s.formulario}>
            <Text style={s.label}>Origem</Text>
            <TextInput value={origem} onChangeText={t => {setOrigem(t); setCoords(null);}} placeholder="Rua, estação ou endereço de saída" placeholderTextColor="#9ba5bd" style={s.input} accessibilityLabel="Origem da viagem" />
            <Pressable onPress={usarLocalizacao} style={s.localizacao} disabled={buscando} accessibilityRole="button">
              {buscando ? <ActivityIndicator color="#625ec2" /> : <Ionicons name="locate-outline" color="#625ec2" size={19} />}
              <Text style={s.localizacaoTexto}>Utilizar minha localização atual</Text>
            </Pressable>
            <Text style={s.label}>Destino</Text>
            <TextInput value={destino} onChangeText={setDestino} placeholder="Para onde você quer ir?" placeholderTextColor="#9ba5bd" style={s.input} accessibilityLabel="Destino da viagem" />
            <Pressable onPress={abrirRotas} style={s.botao} accessibilityRole="button">
              <Ionicons name="navigate-outline" color="#fff" size={20} />
              <Text style={s.botaoTexto}>Traçar percurso e ver tempo estimado</Text>
            </Pressable>
            {!!erro && <Text style={s.erro}>{erro}</Text>}
          </View>
          <View style={s.mapaTopo}>
            <Text style={s.mapaTitulo}>Mapa da região</Text>
            <Text style={s.mapaTexto}>Prévia interativa da área de origem. O trajeto e a previsão de chegada são calculados ao abrir o Google Maps.</Text>
          </View>
          <View style={s.mapa}>
            <View style={s.mapaIcone}><Ionicons name="map-outline" size={45} color="#7481b4" /></View>
            <Text style={s.mapaTexto}>Para visualizar o mapa interativo, abra a opção abaixo.</Text>
            <Pressable onPress={() => Linking.openURL(mapaPreview)} style={s.mapaAbrir}>
              <Text style={s.mapaAbrirTexto}>Abrir mapa da região</Text>
              <Ionicons name="open-outline" color="#625ec2" size={17} />
            </Pressable>
          </View>
          <Pressable onPress={() => Linking.openURL(atual.mapa)} style={s.mapaOficial}>
            <Ionicons name="git-network-outline" color="#5859b0" size={20} />
            <View style={{ flex: 1 }}>
              <Text style={s.mapaOficialTitulo}>{atual.mapaNome}</Text>
              <Text style={s.mapaOficialSub}>{atual.id === "ferroviario" ? "Linhas, estações e integrações" : atual.id === "onibus" ? "Pesquisa e informações de ônibus" : "Mapa de ruas"}</Text>
            </View>
            <Ionicons name="open-outline" color="#5859b0" size={18} />
          </Pressable>
        </View> : <View style={s.instrucao}><Ionicons name="hand-left-outline" color="#6a6abd" size={23} /><Text style={s.instrucaoTexto}>Clique em uma das fotos para começar a planejar seu deslocamento.</Text></View>}

        <View style={s.seguranca}>
          <Ionicons name="shield-outline" color="#6968ba" size={25} />
          <View style={{ flex: 1 }}>
            <Text style={s.segurancaTitulo}>Indicadores de segurança por região</Text>
            <Text style={s.segurancaTexto}>Em desenvolvimento. A futura camada apresentará indicadores agregados, período de referência e fonte oficial — sem classificar rotas ou pessoas como seguras ou perigosas sem evidências.</Text>
          </View>
        </View>
        <Text style={s.footer}>Citizen Mobilidade · Protótipo FIAP Global Solution 2026</Text>
      </View>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  background: { backgroundColor: "#eef1fd", flex: 1 },
  page: { padding: 20, alignItems: "center", paddingBottom: 60 },
  container: { width: "100%", maxWidth: 1090 },
  voltar: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 25 },
  voltarTexto: { color: "#5666a4", fontWeight: "700", fontSize: 13 },
  topo: { marginBottom: 28 },
  supertitulo: { letterSpacing: 2, fontSize: 11, color: "#6c71b5", fontWeight: "800", marginBottom: 12 },
  titulo: { color: "#35466f", fontWeight: "800", fontSize: 37, lineHeight: 45 },
  tituloMobile: { fontSize: 29, lineHeight: 38 },
  destaque: { color: "#7568cc" },
  subtitulo: { color: "#7583a3", fontSize: 15, lineHeight: 24, marginTop: 12 },
  cards: { flexDirection: "row", flexWrap: "wrap", gap: 16 },
  card: { flex: 1, minWidth: 230, backgroundColor: "#fff", borderRadius: 24, overflow: "hidden", borderWidth: 2, borderColor: "transparent" },
  cardMobile: { minWidth: "100%" },
  cardAtivo: { borderColor: "#7264d0" },
  imagem: { height: 183, justifyContent: "flex-start", alignItems: "flex-start", padding: 13 },
  foto: { borderTopLeftRadius: 21, borderTopRightRadius: 21 },
  iconeFoto: { width: 42, height: 42, backgroundColor: "rgba(56,63,111,.78)", borderRadius: 14, alignItems: "center", justifyContent: "center" },
  cardCorpo: { padding: 20 },
  cardTitulo: { fontSize: 20, fontWeight: "800", color: "#394b79" },
  cardLegenda: { fontSize: 13, color: "#8591aa", marginTop: 8, minHeight: 35, lineHeight: 20 },
  cardRodape: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginTop: 17 },
  escolher: { color: "#6764bd", fontSize: 13, fontWeight: "700" },
  instrucao: { padding: 25, marginTop: 25, borderRadius: 22, backgroundColor: "#fff", flexDirection: "row", alignItems: "center", gap: 12 },
  instrucaoTexto: { color: "#7281a2", flex: 1, lineHeight: 22 },
  painel: { marginTop: 27, padding: 23, backgroundColor: "#fff", borderRadius: 24 },
  painelCabecalho: { flexDirection: "row", alignItems: "center", gap: 12 },
  painelIcone: { backgroundColor: "#f0eeff", padding: 14, borderRadius: 15 },
  painelTitulo: { fontSize: 19, color: "#394b79", fontWeight: "800" },
  painelSub: { color: "#8491ab", fontSize: 13, marginTop: 5 },
  formulario: { marginTop: 18 },
  label: { color: "#51618c", fontWeight: "700", fontSize: 13, marginTop: 12, marginBottom: 8 },
  input: { color: "#3c4e79", borderColor: "#e5e9f3", borderWidth: 1, borderRadius: 13, padding: 14, fontSize: 15 },
  localizacao: { flexDirection: "row", alignItems: "center", gap: 8, alignSelf: "flex-start", marginTop: 12, marginBottom: 8 },
  localizacaoTexto: { color: "#635fb6", fontSize: 13, fontWeight: "700" },
  botao: { flexDirection: "row", backgroundColor: "#6862c4", padding: 17, borderRadius: 14, marginTop: 22, alignItems: "center", justifyContent: "center", gap: 9 },
  botaoTexto: { color: "#fff", fontWeight: "800", textAlign: "center", fontSize: 14 },
  erro: { color: "#b64b60", marginTop: 13, fontSize: 13 },
  mapaTopo: { marginTop: 30, marginBottom: 14 },
  mapaTitulo: { color: "#394b79", fontWeight: "800", fontSize: 19 },
  mapaTexto: { color: "#7a88a6", lineHeight: 21, fontSize: 13, marginTop: 6, textAlign: "center" },
  mapa: { minHeight: 220, borderRadius: 19, backgroundColor: "#eff2fb", padding: 20, alignItems: "center", justifyContent: "center" },
  mapaIcone: { marginBottom: 7 },
  mapaAbrir: { backgroundColor: "#fff", padding: 13, borderRadius: 12, marginTop: 17, flexDirection: "row", alignItems: "center", gap: 8 },
  mapaAbrirTexto: { color: "#625ec2", fontWeight: "700", fontSize: 13 },
  mapaOficial: { marginTop: 15, backgroundColor: "#f5f3ff", padding: 17, borderRadius: 17, flexDirection: "row", alignItems: "center", gap: 13 },
  mapaOficialTitulo: { color: "#4f549e", fontWeight: "800", fontSize: 14 },
  mapaOficialSub: { color: "#808aaf", marginTop: 5, fontSize: 12 },
  seguranca: { marginTop: 25, padding: 24, borderRadius: 24, backgroundColor: "#e8e8fb", flexDirection: "row", gap: 13, alignItems: "flex-start" },
  segurancaTitulo: { color: "#4b518a", fontWeight: "800", fontSize: 17 },
  segurancaTexto: { color: "#777f9f", fontSize: 13, lineHeight: 21, marginTop: 7 },
  footer: { marginTop: 35, textAlign: "center", color: "#9ba5bd", fontSize: 12 },
});
