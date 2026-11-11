import React, { useState } from "react";
import {
  ActivityIndicator, Pressable, ScrollView, StyleSheet,
  Text, TextInput, useWindowDimensions, View,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";

const API = (process.env.EXPO_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

type Fonte = { referencia: string; data_verificacao: string };
type Consulta = {
  status: string; resposta: string; fontes: Fonte[]; relacionados: string[];
};
type Trecho = { tipo: string; de: string; para: string; linha?: string; distancia_m?: number };
type Rota = {
  ordem: number; tempo_total_min: number; custo?: { centavos: number | null };
  caminhada_m: number; baldeacoes: number; trechos: Trecho[]; motivos?: string[];
};
type RespostaRotas = {
  modo: string; aviso: string;
  resultado: { rotas?: Rota[]; erro?: { mensagem?: string }; aviso?: string };
};
type Tab = "orientacoes" | "rotas";
type Icone = React.ComponentProps<typeof Ionicons>["name"];

const temas: { nome: string; pergunta: string; icone: Icone; descricao: string }[] = [
  { nome: "Cartões", pergunta: "Como emitir cartão de transporte?", icone: "card-outline", descricao: "Emissão e cadastro" },
  { nome: "Gratuidade", pergunta: "Como solicitar gratuidade no transporte?", icone: "people-outline", descricao: "Benefícios e critérios" },
  { nome: "Acessibilidade", pergunta: "Quais são os direitos de acessibilidade?", icone: "accessibility-outline", descricao: "Mobilidade para todos" },
  { nome: "Direitos", pergunta: "Onde reclamar sobre transporte público?", icone: "shield-checkmark-outline", descricao: "Canais de atendimento" },
];

// Pontos sintéticos da rede em src/rede_demo.py, NÃO são paradas reais.
const R = 6371000;
const LAT0 = -23.55;
const LON0 = -46.63;
function ponto(x: number, y: number) {
  return {
    lat: LAT0 + y / (R * Math.PI / 180),
    lon: LON0 + x / ((R * Math.PI / 180) * Math.cos(LAT0 * Math.PI / 180)),
  };
}
const locais = [
  { nome: "Alfa (simulado)", coords: ponto(0, -100) },
  { nome: "Beta (simulado)", coords: ponto(2000, 100) },
  { nome: "Destino (simulado)", coords: ponto(4000, 300) },
];

export default function Home() {
  const router = useRouter();
  const { width } = useWindowDimensions();
  const compacto = width < 640;
  const [aba, setAba] = useState<Tab>("orientacoes");
  const [pergunta, setPergunta] = useState("");
  const [consulta, setConsulta] = useState<Consulta | null>(null);
  const [rotas, setRotas] = useState<RespostaRotas | null>(null);
  const [origem, setOrigem] = useState(0);
  const [destino, setDestino] = useState(2);
  const [perfil, setPerfil] = useState("padrao");
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState("");

  async function enviar(endpoint: string, body: unknown) {
    const resposta = await fetch(API + endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!resposta.ok) {
      const detalhe = await resposta.json().catch(() => ({}));
      throw new Error(typeof detalhe.detail === "string" ? detalhe.detail : "Servidor indisponível.");
    }
    return resposta.json();
  }

  async function consultar(texto = pergunta) {
    if (!texto.trim()) {
      setErro("Digite sua pergunta antes de consultar.");
      return;
    }
    setAba("orientacoes");
    setPergunta(texto);
    setErro("");
    setConsulta(null);
    setCarregando(true);
    try {
      setConsulta(await enviar("/consultar", { pergunta: texto.trim(), modelo: "B" }));
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Não foi possível conectar à API.");
    } finally {
      setCarregando(false);
    }
  }

  async function buscarRotas() {
    setAba("rotas");
    setErro("");
    setRotas(null);
    if (origem === destino) {
      setErro("Selecione pontos de origem e destino diferentes.");
      return;
    }
    setCarregando(true);
    try {
      // Data fixa para reproduzir a rede fictícia; não representa horários atuais.
      setRotas(await enviar("/rotas", {
        origem: locais[origem].coords,
        destino: locais[destino].coords,
        partida: "2026-11-09T08:00:00",
        necessidades: { perfil_tarifario: perfil },
      }));
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Não foi possível calcular a rota.");
    } finally {
      setCarregando(false);
    }
  }

  const botaoAba = (id: Tab, rotulo: string, icone: Icone) => (
    <Pressable
      onPress={() => { setAba(id); setErro(""); }}
      accessibilityRole="tab"
      accessibilityState={{ selected: aba === id }}
      style={[s.tab, aba === id && s.tabAtiva]}
    >
      <Ionicons name={icone} size={18} color={aba === id ? "#fff" : "#5b6d9c"} />
      <Text style={[s.tabTexto, aba === id && s.tabTextoAtivo]}>{rotulo}</Text>
    </Pressable>
  );

  return (
    <ScrollView style={s.fundo} contentContainerStyle={s.pagina}>
      <View style={s.container}>
        <View style={s.topo}>
          <View style={s.marcaIcone}><Ionicons name="navigate" size={19} color="#fff" /></View>
          <View>
            <Text style={s.marca}>citizen<Text style={s.marcaDestaque}>mobilidade</Text></Text>
            <Text style={s.marcaLegenda}>GLOBAL SOLUTION 2026</Text>
          </View>
          <View style={s.selo}><Text style={s.seloTexto}>Protótipo acadêmico</Text></View>
        </View>

        <View style={[s.hero, compacto && s.heroCompacto]}>
          <View style={s.heroTexto}>
            <View style={s.tag}><Ionicons name="sparkles-outline" size={13} color="#4f63b2" /><Text style={s.tagTexto}>Mobilidade com informação</Text></View>
            <Text style={[s.titulo, compacto && s.tituloPequeno]}>Sua cidade,{"\n"}<Text style={s.tituloRoxo}>mais acessível.</Text></Text>
            <Text style={s.subtitulo}>Tire dúvidas sobre transporte, conheça seus direitos e explore trajetos de demonstração em um só lugar.</Text>
          </View>
          {!compacto && <View style={s.ilustracao}>
            <Ionicons name="train-outline" size={78} color="#6c7cc5" />
            <View style={s.ilustracaoSelo}><Ionicons name="checkmark-circle" color="#625ec4" size={18} /><Text style={s.ilustracaoTexto}>Informação clara</Text></View>
          </View>}
        </View>

        <View style={s.tabs}>{botaoAba("orientacoes", "Assistente cidadão", "chatbubbles-outline")}{botaoAba("rotas", "Planejar rota", "map-outline")}</View>

        <Pressable onPress={() => router.push("/mobilidade")} style={s.mobilidadeLink} accessibilityRole="button">
          <Ionicons name="train-outline" size={23} color="#6762bd" />
          <View style={{ flex: 1 }}><Text style={s.mobilidadeTitulo}>Explorar transportes e mapas</Text><Text style={s.mobilidadeSub}>Trem, metrô, ônibus e a pé · fotos, localização e trajetos</Text></View>
          <Ionicons name="chevron-forward" size={19} color="#6762bd" />
        </Pressable>
        {aba === "orientacoes" ? <>
          <View style={s.secaoCabecalho}><Text style={s.secaoTitulo}>Como podemos ajudar?</Text><Text style={s.secaoDescricao}>Pesquise informações de forma simples.</Text></View>
          <View style={s.busca}>
            <Ionicons name="search-outline" size={22} color="#7786ad" />
            <TextInput
              style={s.campo} value={pergunta} onChangeText={setPergunta}
              placeholder="Digite sua dúvida sobre mobilidade..."
              placeholderTextColor="#8b96b3"
              returnKeyType="search" onSubmitEditing={() => consultar()}
              accessibilityLabel="Pergunta sobre mobilidade"
            />
            <Pressable style={s.buscarBotao} onPress={() => consultar()} accessibilityRole="button" accessibilityLabel="Consultar">
              <Ionicons name="arrow-forward" size={21} color="#fff" />
            </Pressable>
          </View>
          <View style={s.secaoCabecalho}><Text style={s.secaoTitulo}>Explore por assunto</Text><Text style={s.secaoDescricao}>Escolha um tema para começar.</Text></View>
          <View style={s.grade}>{temas.map(t => (
            <Pressable key={t.nome} onPress={() => consultar(t.pergunta)} style={[s.tema, compacto && s.temaPequeno]} accessibilityRole="button">
              <View style={s.temaIcone}><Ionicons name={t.icone} size={25} color="#5b67bd" /></View>
              <Text style={s.temaNome}>{t.nome}</Text><Text style={s.temaDescricao}>{t.descricao}</Text>
              <Ionicons name="arrow-forward-outline" size={18} color="#7b8bb4" style={s.temaSeta} />
            </Pressable>
          ))}</View>
          <View style={s.resultado}>
            <Text style={s.resultadoTitulo}>Resposta do assistente</Text>
            {!consulta && !carregando && <Text style={s.resultadoTexto}>Faça uma pergunta para visualizar as orientações e suas referências.</Text>}
            {consulta && <>
              <Text style={s.resultadoTexto}>{consulta.resposta}</Text>
              {consulta.fontes?.map((f, i) => (
                <View key={i} style={s.fonte}><Ionicons name="link-outline" size={15} color="#6275b2" /><Text selectable style={s.fonteTexto}>{f.referencia} · verificado em {f.data_verificacao}</Text></View>
              ))}
              {consulta.relacionados?.length > 0 && <Text style={s.relacionados}>Assuntos relacionados: {consulta.relacionados.join(", ")}</Text>}
            </>}
          </View>
        </> : <>
          <View style={s.secaoCabecalho}><Text style={s.secaoTitulo}>Planeje seu trajeto</Text><Text style={s.secaoDescricao}>Teste o algoritmo de rotas usando pontos fictícios.</Text></View>
          <View style={s.aviso}><Ionicons name="information-circle-outline" size={21} color="#785a22" /><Text style={s.avisoTexto}>Modo demonstração: paradas, horários e tarifas são simulados. Não use para uma viagem real.</Text></View>
          <View style={s.painelRotas}>
            <Text style={s.campoLabel}>Origem</Text>
            <View style={s.opcoes}>{locais.map((local, i) => (
              <Pressable key={local.nome} style={[s.opcao, origem === i && s.opcaoAtiva]} onPress={() => setOrigem(i)} accessibilityRole="radio" accessibilityState={{ checked: origem === i }}>
                <Text style={[s.opcaoTexto, origem === i && s.opcaoTextoAtivo]}>{local.nome}</Text>
              </Pressable>
            ))}</View>
            <Text style={s.campoLabel}>Destino</Text>
            <View style={s.opcoes}>{locais.map((local, i) => (
              <Pressable key={local.nome} style={[s.opcao, destino === i && s.opcaoAtiva]} onPress={() => setDestino(i)} accessibilityRole="radio" accessibilityState={{ checked: destino === i }}>
                <Text style={[s.opcaoTexto, destino === i && s.opcaoTextoAtivo]}>{local.nome}</Text>
              </Pressable>
            ))}</View>
            <Text style={s.campoLabel}>Perfil de tarifa simulada</Text>
            <View style={s.opcoes}>{[["padrao", "Padrão"], ["estudante", "Estudante"]].map(([id, nome]) => (
              <Pressable key={id} style={[s.opcao, perfil === id && s.opcaoAtiva]} onPress={() => setPerfil(id)}>
                <Text style={[s.opcaoTexto, perfil === id && s.opcaoTextoAtivo]}>{nome}</Text>
              </Pressable>
            ))}</View>
            <Pressable style={s.botaoRota} onPress={buscarRotas}><Ionicons name="navigate-outline" size={18} color="#fff" /><Text style={s.botaoRotaTexto}>Comparar rotas simuladas</Text></Pressable>
          </View>
          {rotas && <View style={s.listaRotas}>
            <Text style={s.resultadoTitulo}>Resultado da simulação</Text>
            {!!rotas.resultado.erro && <Text style={s.resultadoTexto}>{rotas.resultado.erro.mensagem}</Text>}
            {(rotas.resultado.rotas || []).map((rota, i) => (
              <View style={s.rotaCard} key={rota.ordem || i}>
                <Text style={s.rotaNome}>Opção {rota.ordem}</Text>
                <Text style={s.rotaMetricas}>{rota.tempo_total_min} min  ·  {rota.custo?.centavos == null ? "Tarifa não confirmada" : `R$ ${(rota.custo.centavos / 100).toFixed(2).replace(".", ",")}`}</Text>
                <Text style={s.rotaDetalhe}>{rota.caminhada_m} m a pé  ·  {rota.baldeacoes} baldeação(ões)</Text>
                {rota.trechos?.map((trecho, idx) => <Text key={idx} style={s.trecho}>• {trecho.tipo === "transporte" ? trecho.linha + ": " : trecho.tipo + ": "}{trecho.de} → {trecho.para}</Text>)}
              </View>
            ))}
            <Text style={s.relacionados}>{rotas.aviso} {rotas.resultado.aviso || ""}</Text>
          </View>}
        </>}

        {carregando && <View style={s.estado}><ActivityIndicator color="#625fc4" /><Text style={s.estadoTexto}>Consultando...</Text></View>}
        {!!erro && <View style={s.erro}><Ionicons name="alert-circle-outline" color="#b8475a" size={20} /><Text style={s.erroTexto}>{erro}</Text></View>}
        <Text style={s.rodape}>Citizen Mobilidade · FIAP 2026{"\n"}Projeto acadêmico independente. Consulte os canais oficiais antes de tomar decisões.</Text>
      </View>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  mobilidadeLink: { backgroundColor: "#fff", borderRadius: 18, padding: 18, marginTop: 18, flexDirection: "row", alignItems: "center", gap: 12 },
  mobilidadeTitulo: { color: "#424a86", fontWeight: "800", fontSize: 15 },
  mobilidadeSub: { color: "#8894b0", fontSize: 12, marginTop: 5 },
  fundo: { flex: 1, backgroundColor: "#edf1ff" },
  pagina: { minHeight: "100%", paddingVertical: 24, paddingHorizontal: 14, alignItems: "center" },
  container: { maxWidth: 1040, width: "100%", paddingBottom: 20 },
  topo: { flexDirection: "row", alignItems: "center", marginBottom: 25, gap: 10, flexWrap: "wrap" },
  marcaIcone: { width: 40, height: 40, borderRadius: 13, alignItems: "center", justifyContent: "center", backgroundColor: "#6863c8" },
  marca: { color: "#344777", fontSize: 19, fontWeight: "800" },
  marcaDestaque: { color: "#716bd1" },
  marcaLegenda: { fontSize: 9, color: "#8491b1", letterSpacing: 1.4, fontWeight: "700" },
  selo: { marginLeft: "auto", paddingHorizontal: 12, paddingVertical: 8, backgroundColor: "#fff", borderRadius: 20 },
  seloTexto: { color: "#7885a7", fontSize: 11, fontWeight: "700" },
  hero: { backgroundColor: "#dfe5ff", borderRadius: 28, padding: 35, flexDirection: "row", alignItems: "center", justifyContent: "space-between", overflow: "hidden" },
  heroCompacto: { padding: 23 },
  heroTexto: { flex: 1 },
  tag: { backgroundColor: "#fff", paddingHorizontal: 12, paddingVertical: 7, alignSelf: "flex-start", borderRadius: 30, flexDirection: "row", alignItems: "center", gap: 7, marginBottom: 19 },
  tagTexto: { color: "#5568a8", fontWeight: "600", fontSize: 12 },
  titulo: { color: "#344576", fontSize: 43, fontWeight: "800", lineHeight: 51 },
  tituloPequeno: { fontSize: 33, lineHeight: 41 },
  tituloRoxo: { color: "#7164ca" },
  subtitulo: { fontSize: 15, color: "#677798", lineHeight: 23, marginTop: 13, maxWidth: 530 },
  ilustracao: { width: 240, alignItems: "center", justifyContent: "center", gap: 21 },
  ilustracaoSelo: { borderRadius: 16, backgroundColor: "#fff", paddingHorizontal: 14, paddingVertical: 11, flexDirection: "row", gap: 8, alignItems: "center" },
  ilustracaoTexto: { fontWeight: "700", color: "#6574a9", fontSize: 12 },
  tabs: { flexDirection: "row", marginTop: 24, backgroundColor: "#fff", borderRadius: 17, padding: 5, gap: 5, alignSelf: "flex-start", flexWrap: "wrap" },
  tab: { paddingHorizontal: 17, paddingVertical: 12, borderRadius: 13, flexDirection: "row", alignItems: "center", gap: 7 },
  tabAtiva: { backgroundColor: "#6767c7" },
  tabTexto: { color: "#596b97", fontSize: 13, fontWeight: "700" },
  tabTextoAtivo: { color: "#fff" },
  secaoCabecalho: { marginTop: 26, marginBottom: 13 },
  secaoTitulo: { color: "#334674", fontSize: 22, fontWeight: "800" },
  secaoDescricao: { color: "#7b88a6", fontSize: 13, marginTop: 5 },
  busca: { flexDirection: "row", alignItems: "center", borderRadius: 17, backgroundColor: "#fff", paddingHorizontal: 15, minHeight: 63, gap: 9 },
  campo: { flex: 1, color: "#39496d", fontSize: 15, paddingVertical: 10, minWidth: 0 },
  buscarBotao: { width: 39, height: 39, borderRadius: 12, backgroundColor: "#6765c7", alignItems: "center", justifyContent: "center" },
  grade: { flexDirection: "row", flexWrap: "wrap", gap: 14 },
  tema: { width: "23%", flexGrow: 1, minWidth: 165, backgroundColor: "#fff", borderRadius: 21, padding: 20, minHeight: 155 },
  temaPequeno: { width: "45%", minWidth: 135 },
  temaIcone: { backgroundColor: "#eef0ff", width: 48, height: 48, borderRadius: 14, alignItems: "center", justifyContent: "center", marginBottom: 11 },
  temaNome: { fontSize: 15, fontWeight: "800", color: "#3a4e7b" },
  temaDescricao: { fontSize: 12, marginTop: 5, color: "#8a96af" },
  temaSeta: { position: "absolute", right: 17, top: 19 },
  resultado: { backgroundColor: "#fff", padding: 24, borderRadius: 22, marginTop: 25 },
  resultadoTitulo: { fontSize: 18, fontWeight: "800", color: "#3a4b7a", marginBottom: 12 },
  resultadoTexto: { color: "#5e6e91", lineHeight: 24, fontSize: 15 },
  fonte: { flexDirection: "row", gap: 8, paddingVertical: 10, alignItems: "center", flexWrap: "wrap" },
  fonteTexto: { color: "#546aaa", fontSize: 13, flexShrink: 1 },
  relacionados: { color: "#8290aa", fontSize: 12, marginTop: 10, lineHeight: 20 },
  aviso: { backgroundColor: "#fff4dc", borderRadius: 15, padding: 16, gap: 10, flexDirection: "row", alignItems: "center" },
  avisoTexto: { color: "#81652d", flex: 1, lineHeight: 20, fontSize: 13 },
  painelRotas: { backgroundColor: "#fff", borderRadius: 22, padding: 23, marginTop: 18 },
  campoLabel: { fontSize: 14, color: "#3e4f7c", fontWeight: "800", marginTop: 10, marginBottom: 11 },
  opcoes: { flexDirection: "row", flexWrap: "wrap", gap: 9, marginBottom: 12 },
  opcao: { borderRadius: 12, paddingHorizontal: 13, paddingVertical: 11, backgroundColor: "#f0f2fa", borderWidth: 1, borderColor: "#e6e9f5" },
  opcaoAtiva: { backgroundColor: "#e8e5ff", borderColor: "#8174d0" },
  opcaoTexto: { color: "#6a7899", fontSize: 13, fontWeight: "600" },
  opcaoTextoAtivo: { color: "#5950b8" },
  botaoRota: { backgroundColor: "#6865c8", paddingVertical: 15, paddingHorizontal: 20, borderRadius: 15, marginTop: 13, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 9 },
  botaoRotaTexto: { color: "#fff", fontWeight: "800", fontSize: 14 },
  listaRotas: { backgroundColor: "#fff", borderRadius: 22, padding: 22, marginTop: 20 },
  rotaCard: { backgroundColor: "#f6f7ff", borderRadius: 17, padding: 17, marginBottom: 12 },
  rotaNome: { fontWeight: "800", fontSize: 16, color: "#394b7c" },
  rotaMetricas: { fontWeight: "700", color: "#6156b9", fontSize: 15, marginTop: 9 },
  rotaDetalhe: { color: "#7584a1", marginTop: 7, fontSize: 13 },
  trecho: { color: "#667593", marginTop: 8, lineHeight: 19, fontSize: 12 },
  estado: { flexDirection: "row", gap: 10, padding: 16, alignItems: "center", justifyContent: "center" },
  estadoTexto: { color: "#646eac" },
  erro: { backgroundColor: "#fff0f0", borderRadius: 15, padding: 15, flexDirection: "row", alignItems: "center", gap: 9, marginTop: 15 },
  erroTexto: { color: "#b8475a", flex: 1, fontSize: 13 },
  rodape: { color: "#8894b1", textAlign: "center", fontSize: 11, lineHeight: 19, marginTop: 27 },
});
