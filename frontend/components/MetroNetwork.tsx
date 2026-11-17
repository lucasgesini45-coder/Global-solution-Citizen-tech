import React, { useState } from "react";
import { Image, Linking, Pressable, ScrollView, StyleSheet, Text, TextInput, View, useWindowDimensions } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const PAGINA_MAPA = "https://www.metro.sp.gov.br/sua-viagem/mapa-da-rede/";
const PDF_MAPA = "https://www.metro.sp.gov.br/wp-content/uploads/2026/07/mapa-da-rede.pdf";
// Imagem do documento oficial, espelhada em formato WEBP pelo Trilhos Agora.
const MAPA_IMAGEM = "https://trilhosagora.com.br/mapa-metro-cptm-sao-paulo.webp";
const TARIFAS = "https://www.metro.sp.gov.br/sua-viagem/bilhetes-cartoes/";
const TARIFAS_SPTRANS = "https://www.sptrans.com.br/tarifas";
const HORARIOS = "https://www.metro.sp.gov.br/sua-viagem/horarios/";
const ESTADO = "https://www.metro.sp.gov.br/sua-viagem/direto-metro/";
const OPERADORES: Record<string,string> = {
 "Metrô":"https://www.metro.sp.gov.br/",
 "Motiva":"https://trilhos.motiva.com.br/",
 "Linha Uni":"https://www.linhauni.com.br/",
 "TIC Trens":"https://www.tictrens.com.br/",
 "CPTM":"https://www.cptm.sp.gov.br/",
 "Trivia":"https://www.triviatrens.com.br/",
};
type Linha = {numero:string;nome:string;cor:string;operador:string;extremos:string;tipo:"metro"|"trem"|"monotrilho"};

// Referência: mapa oficial do transporte metropolitano, edição julho/2026.
// Os dados descrevem a rede no documento, não a operação em tempo real.
const LINHAS: Linha[] = [
 {numero:"1",nome:"Azul",cor:"#0455A1",operador:"Metrô",extremos:"Jabaquara · Tucuruvi",tipo:"metro"},
 {numero:"2",nome:"Verde",cor:"#008E5A",operador:"Metrô",extremos:"Vila Madalena · Vila Prudente",tipo:"metro"},
 {numero:"3",nome:"Vermelha",cor:"#ED1C24",operador:"Metrô",extremos:"Palmeiras-Barra Funda · Corinthians-Itaquera",tipo:"metro"},
 {numero:"4",nome:"Amarela",cor:"#F9C80E",operador:"Motiva",extremos:"Vila Sônia · Luz",tipo:"metro"},
 {numero:"5",nome:"Lilás",cor:"#9B3894",operador:"Motiva",extremos:"Capão Redondo · Chácara Klabin",tipo:"metro"},
 {numero:"6",nome:"Laranja",cor:"#F47920",operador:"Linha Uni",extremos:"João Paulo I · Perdizes (operação assistida)",tipo:"metro"},
 {numero:"7",nome:"Rubi",cor:"#A6192E",operador:"TIC Trens",extremos:"Palmeiras-Barra Funda · Jundiaí",tipo:"trem"},
 {numero:"8",nome:"Diamante",cor:"#8F9498",operador:"Motiva",extremos:"Júlio Prestes · Amador Bueno",tipo:"trem"},
 {numero:"9",nome:"Esmeralda",cor:"#008A72",operador:"Motiva",extremos:"Osasco · Varginha",tipo:"trem"},
 {numero:"10",nome:"Turquesa",cor:"#008F95",operador:"CPTM",extremos:"Palmeiras-Barra Funda · Rio Grande da Serra",tipo:"trem"},
 {numero:"11",nome:"Coral",cor:"#F36C38",operador:"Trivia",extremos:"Palmeiras-Barra Funda · Estudantes",tipo:"trem"},
 {numero:"12",nome:"Safira",cor:"#153E84",operador:"Trivia",extremos:"Brás · Calmon Viana",tipo:"trem"},
 {numero:"13",nome:"Jade",cor:"#00A5A5",operador:"Trivia",extremos:"Eng. Goulart · Aeroporto-Guarulhos",tipo:"trem"},
 {numero:"15",nome:"Prata",cor:"#8C98A3",operador:"Metrô",extremos:"Vila Prudente · Jardim Colonial",tipo:"monotrilho"},
 {numero:"17",nome:"Ouro",cor:"#B89035",operador:"Metrô",extremos:"Morumbi · Aeroporto de Congonhas / Washington Luís",tipo:"monotrilho"},
];
// Estações do mapa oficial de julho de 2026 (nomes abreviados quando necessário).
// A lista é informativa; não confirma funcionamento de uma estação.
const ESTACOES: Record<string,string[]> = {
  "1": [
    "Jabaquara",
    "Conceição",
    "São Judas",
    "Saúde",
    "Praça da Árvore",
    "Santa Cruz",
    "Vila Mariana",
    "Ana Rosa",
    "Paraíso",
    "Vergueiro",
    "São Joaquim",
    "Japão-Liberdade",
    "Sé",
    "São Bento",
    "Luz",
    "Tiradentes",
    "Armênia",
    "Portuguesa-Tietê",
    "Carandiru",
    "Santana",
    "Jardim São Paulo-Ayrton Senna",
    "Parada Inglesa",
    "Tucuruvi"
  ],
  "2": [
    "Vila Madalena",
    "Sumaré",
    "Clínicas",
    "Consolação",
    "Trianon-Masp",
    "Brigadeiro",
    "Paraíso",
    "Ana Rosa",
    "Chácara Klabin",
    "Santos-Imigrantes",
    "Alto do Ipiranga",
    "Sacomã",
    "Tamanduateí",
    "Vila Prudente"
  ],
  "3": [
    "Palmeiras-Barra Funda",
    "Marechal Deodoro",
    "Santa Cecília",
    "República",
    "Anhangabaú",
    "Sé",
    "Pedro II",
    "Brás",
    "Bresser-Mooca",
    "Belém",
    "Carrão",
    "Tatuapé",
    "Penha",
    "Vila Matilde",
    "Guilhermina-Esperança",
    "Patriarca-Vila Ré",
    "Artur Alvim",
    "Corinthians-Itaquera"
  ],
  "4": [
    "Vila Sônia",
    "São Paulo-Morumbi",
    "Butantã",
    "Pinheiros",
    "Faria Lima",
    "Fradique Coutinho",
    "Oscar Freire",
    "Paulista",
    "Higienópolis-Mackenzie",
    "República",
    "Luz"
  ],
  "5": [
    "Capão Redondo",
    "Campo Limpo",
    "Vila das Belezas",
    "Giovanni Gronchi",
    "Santo Amaro",
    "Largo Treze",
    "Adolfo Pinheiro",
    "Alto da Boa Vista",
    "Borba Gato",
    "Brooklin",
    "Campo Belo",
    "Eucaliptos",
    "Moema",
    "AACD-Servidor",
    "Hospital São Paulo",
    "Santa Cruz",
    "Chácara Klabin"
  ],
  "6": [
    "João Paulo I",
    "Freguesia do Ó",
    "Santa Marina",
    "Água Branca",
    "SESC-Pompeia",
    "Perdizes"
  ],
  "7": [
    "Palmeiras-Barra Funda",
    "Água Branca",
    "Lapa",
    "Piqueri",
    "Pirituba",
    "Vila Clarice",
    "Jaraguá",
    "Vila Aurora",
    "Perus",
    "Caieiras",
    "Franco da Rocha",
    "Baltazar Fidélis",
    "Francisco Morato",
    "Botujuru",
    "Campo Limpo Paulista",
    "Várzea Paulista",
    "Jundiaí"
  ],
  "8": [
    "Júlio Prestes",
    "Palmeiras-Barra Funda",
    "Lapa",
    "Domingos de Moraes",
    "Imperatriz Leopoldina",
    "Presidente Altino",
    "Osasco",
    "Comandante Sampaio",
    "Quitaúna",
    "General Miguel Costa",
    "Carapicuíba",
    "Santa Terezinha",
    "Antônio João",
    "Barueri",
    "Jardim Belval",
    "Jardim Silveira",
    "Jandira",
    "Sagrado Coração",
    "Engenheiro Cardoso",
    "Itapevi",
    "Santa Rita",
    "Amador Bueno"
  ],
  "9": [
    "Osasco",
    "Presidente Altino",
    "Ceasa",
    "Villa Lobos-Jaguaré",
    "Cidade Universitária",
    "Pinheiros",
    "Hebraica-Rebouças",
    "Cidade Jardim",
    "Vila Olímpia",
    "Berrini",
    "Morumbi",
    "Granja Julieta",
    "João Dias",
    "Santo Amaro",
    "Socorro",
    "Jurubatuba",
    "Autódromo",
    "Primavera-Interlagos",
    "Grajaú",
    "Mendes-Vila Natal",
    "Varginha"
  ],
  "10": [
    "Palmeiras-Barra Funda",
    "Luz",
    "Brás",
    "Juventus-Mooca",
    "Ipiranga",
    "Tamanduateí",
    "São Caetano do Sul",
    "Utinga",
    "Prefeito Saladino",
    "Santo André",
    "Capuava",
    "Mauá",
    "Guapituba",
    "Ribeirão Pires",
    "Rio Grande da Serra"
  ],
  "11": [
    "Palmeiras-Barra Funda",
    "Luz",
    "Brás",
    "Tatuapé",
    "Corinthians-Itaquera",
    "Dom Bosco",
    "José Bonifácio",
    "Guaianases",
    "Antônio Gianetti Neto",
    "Ferraz de Vasconcelos",
    "Poá",
    "Calmon Viana",
    "Suzano",
    "Jundiapeba",
    "Braz Cubas",
    "Mogi das Cruzes",
    "Estudantes"
  ],
  "12": [
    "Brás",
    "Tatuapé",
    "Engenheiro Goulart",
    "USP Leste",
    "Comendador Ermelino",
    "São Miguel Paulista",
    "Jardim Helena-Vila Mara",
    "Itaim Paulista",
    "Jardim Romano",
    "Engenheiro Manoel Feio",
    "Itaquaquecetuba",
    "Aracaré",
    "Calmon Viana"
  ],
  "13": [
    "Engenheiro Goulart",
    "Guarulhos-CECAP",
    "Aeroporto-Guarulhos"
  ],
  "15": [
    "Vila Prudente",
    "Oratório",
    "São Lucas",
    "Camilo Haddad",
    "Vila Tolstói",
    "Vila União",
    "Jardim Planalto",
    "Sapopemba",
    "Fazenda da Juta",
    "São Mateus",
    "Jardim Colonial"
  ],
  "17": [
    "Morumbi",
    "Chucri Zaidan",
    "Vila Cordeiro",
    "Campo Belo",
    "Vereador José Diniz",
    "Brooklin Paulista",
    "Aeroporto de Congonhas",
    "Washington Luís"
  ]
};
const gratuita=(numero:string)=>numero==="6"||numero==="17";
const tarifa=(numero:string)=>gratuita(numero)?"R$ 0,00*":"R$ 5,40";
const INTEGRACOES_HORARIAS=["Tatuapé","Corinthians-Itaquera"];
const INTEGRACOES_LIVRES=["Brás","Luz","Palmeiras-Barra Funda","Tamanduateí"];
const TABELA_TARIFAS=[
 ["Unitária / comum","R$ 5,40"],
 ["Vale-transporte","R$ 5,92"],
 ["Estudante / professor (elegíveis)","R$ 2,70"],
 ["Madrugador comum (horário específico)","R$ 4,78"],
 ["Integração ônibus municipal + trilhos","R$ 9,38"],
 ["Integração estudante (elegível)","R$ 5,35"],
];
type Filtro = "todos" | Linha["tipo"];
const filtros: {id:Filtro;label:string}[] = [{id:"todos",label:"Todas"},{id:"metro",label:"Metrô"},{id:"trem",label:"Trem"},{id:"monotrilho",label:"Monotrilho"}];
const normalizar=(s:string)=>s.normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase();

export default function MetroNetwork({mobile}:{mobile:boolean}){
 const [filtro,setFiltro]=useState<Filtro>("todos");
 const [painel,setPainel]=useState<"linhas"|"tarifas">("linhas");
 const [busca,setBusca]=useState("");
 const [selecionada,setSelecionada]=useState<string|null>(null);
 const [erro,setErro]=useState("");
 const [mapaErro,setMapaErro]=useState(false);
 const [tentativa,setTentativa]=useState(0);
 const [zoom,setZoom]=useState(1);
 const [larguraMapa,setLarguraMapa]=useState(600);
 const {height}=useWindowDimensions();
 const alturaPainel=Math.max(600,Math.min(900,Math.round(height-220)));
 const mapaLargura=Math.max(1,larguraMapa)*zoom;
 const abrir=async(url:string)=>{
   setErro("");
   try{await Linking.openURL(url);}catch{setErro("Não foi possível abrir o site oficial. Tente novamente.");}
 };
 const linhas=LINHAS.filter(l=>(filtro==="todos"||l.tipo===filtro)&&normalizar(l.numero+" "+l.nome+" "+l.operador+" "+l.extremos+" "+(ESTACOES[l.numero]||[]).join(" ")).includes(normalizar(busca.trim())));
 return <View style={s.page}>
   <View style={s.intro}>
     <Text style={s.eyebrow}>REDE METROPOLITANA · SÃO PAULO</Text>
     <Text style={s.heading}>Explore a rede de metrô e trens.</Text>
     <Text style={s.subtitle}>Consulte as linhas, integrações e estações no mapa oficial antes de planejar sua viagem.</Text>
   </View>
   <View style={[s.layout,mobile?s.layoutMobile:{height:alturaPainel}]}>
     <View style={[s.mapCard,mobile&&s.mapMobile]}>
       <View style={s.header}><View style={{flex:1}}><Text style={s.title}>Mapa da rede</Text><Text style={s.small}>Documento oficial · julho de 2026</Text></View><Pressable onPress={()=>abrir(PDF_MAPA)} style={s.primary} accessibilityRole="button"><Ionicons name="expand-outline" size={16} color="#fff"/><Text style={s.primaryText}>Abrir PDF</Text></Pressable></View>
       <View style={s.mapTools}>
         <Text style={s.small}>Amplie para ler as estações</Text>
         <View style={s.zoomGroup}>
           <Pressable onPress={()=>setZoom(x=>Math.max(1,x-.5))} accessibilityLabel="Diminuir zoom" style={s.zoomButton}><Ionicons name="remove" size={18} color="#0069d2"/></Pressable>
           <Pressable onPress={()=>setZoom(1)} style={s.zoomButton} accessibilityLabel="Restaurar zoom"><Text style={s.link}>{Math.round(zoom*100)}%</Text></Pressable>
           <Pressable onPress={()=>setZoom(x=>Math.min(3,x+.5))} accessibilityLabel="Aumentar zoom" style={s.zoomButton}><Ionicons name="add" size={18} color="#0069d2"/></Pressable>
         </View>
       </View>
       <View style={[s.mapViewport,mobile&&s.mapViewportMobile]} onLayout={e=>setLarguraMapa(Math.floor(e.nativeEvent.layout.width))}>
         {mapaErro?<View style={s.nativePreview}>
           <Ionicons name="map-outline" color="#0071e3" size={36}/>
           <Text style={s.title}>Imagem indisponível</Text>
           <Text style={s.small}>Recarregue a imagem ou abra o documento oficial em outra aba.</Text>
           <Pressable onPress={()=>{setMapaErro(false);setTentativa(x=>x+1);}} style={s.primary}><Text style={s.primaryText}>Tentar novamente</Text></Pressable>
           <Pressable onPress={()=>abrir(PDF_MAPA)}><Text style={s.link}>Abrir PDF oficial</Text></Pressable>
         </View>:<ScrollView style={{flex:1}} nestedScrollEnabled showsVerticalScrollIndicator persistentScrollbar>
           <ScrollView horizontal nestedScrollEnabled showsHorizontalScrollIndicator persistentScrollbar>
             <Image key={tentativa} source={{uri:tentativa?MAPA_IMAGEM+"?v="+tentativa:MAPA_IMAGEM}} style={{width:mapaLargura,height:mapaLargura*1.5,backgroundColor:"#fff"}} resizeMode="contain" accessibilityLabel="Mapa oficial do transporte metropolitano de São Paulo, julho de 2026" onError={()=>setMapaErro(true)}/>
           </ScrollView>
         </ScrollView>}
       </View>
       <Text style={s.note}>Fonte: mapa oficial STM/Metrô, julho de 2026. Imagem via Trilhos Agora. Mapa esquemático, sem escala. Use o PDF oficial para versão vetorial.</Text>
       <Pressable onPress={()=>abrir(PAGINA_MAPA)} accessibilityRole="link"><Text style={s.link}>Consultar a versão mais recente no site oficial ↗</Text></Pressable>
     </View>
     <View style={[s.details,mobile&&s.detailsMobile]}>
       <View style={s.header}><Text style={s.title}>Rede metropolitana</Text><Text style={s.small}>{painel==="linhas"?linhas.length+" linhas":"Valores 2026"}</Text></View>
       <View style={s.sectionTabs}>
         {(["linhas","tarifas"] as const).map(p=><Pressable key={p} onPress={()=>setPainel(p)} accessibilityRole="tab" accessibilityState={{selected:painel===p}} style={[s.sectionTab,painel===p&&s.sectionTabActive]}><Text style={[s.filterText,painel===p&&s.activeText]}>{p==="linhas"?"Linhas e estações":"Tarifas"}</Text></Pressable>)}
       </View>
       {painel==="linhas"&&<>
       <View style={s.search}><Ionicons name="search-outline" size={17} color="#64748b"/><TextInput value={busca} onChangeText={setBusca} placeholder="Buscar linha ou estação..." placeholderTextColor="#8898a8" style={s.input} accessibilityLabel="Buscar linhas ferroviárias"/></View>
       <View style={s.filters}>{filtros.map(f=><Pressable key={f.id} onPress={()=>setFiltro(f.id)} style={[s.filter,filtro===f.id&&s.active]} accessibilityRole="button" accessibilityState={{selected:filtro===f.id}}><Text style={[s.filterText,filtro===f.id&&s.activeText]}>{f.label}</Text></Pressable>)}</View>
       </>}
       <ScrollView key={painel} style={mobile?undefined:s.lineScroll} contentContainerStyle={s.lineScrollContent} nestedScrollEnabled persistentScrollbar showsVerticalScrollIndicator keyboardShouldPersistTaps="handled">
       {painel==="linhas"&&<>
       {linhas.map(l=><View key={l.numero} style={s.lineGroup}>
         <Pressable onPress={()=>setSelecionada(x=>x===l.numero?null:l.numero)} style={s.line} accessibilityRole="button" accessibilityState={{expanded:selecionada===l.numero}}>
           <View style={[s.number,{backgroundColor:l.cor}]}><Text style={[s.numberText,["4","8","15","17"].includes(l.numero)&&{color:"#172333"}]}>{l.numero}</Text></View>
           <View style={s.lineLabel}><Text style={s.lineName}>Linha {l.numero} – {l.nome}</Text><Text style={s.small}>{l.operador}{gratuita(l.numero)?" · Operação especial":""}</Text></View>
           <Text style={s.fare}>{tarifa(l.numero)}</Text>
           <Ionicons name={selecionada===l.numero?"chevron-up":"chevron-down"} size={16} color="#8797a7"/>
         </Pressable>
         {selecionada===l.numero&&<View style={s.expanded}>
           <Text style={s.extremos}>{l.extremos}</Text>
           <Text style={s.small}>Tarifa comum de embarque por estação</Text>
           {(ESTACOES[l.numero]||[]).map(estacao=><View key={estacao} style={s.station}>
             <View style={{flex:1}}><Text style={s.stationName}>{estacao}</Text>
               {INTEGRACOES_HORARIAS.includes(estacao)&&<Text style={s.note}>Transferência Metrô–trem gratuita em horários específicos.</Text>}
               {INTEGRACOES_LIVRES.includes(estacao)&&<Text style={s.note}>Área de transferência gratuita Metrô–trem.</Text>}
             </View>
             <Text style={s.fare}>{tarifa(l.numero)}</Text>
           </View>)}
           {gratuita(l.numero)&&<Text style={s.note}>* Gratuidade provisória na operação assistida/transitória; consulte o operador. Não inclui outros transportes.</Text>}
           <Pressable onPress={()=>abrir(OPERADORES[l.operador])} accessibilityRole="link"><Text style={s.link}>Informações no operador ↗</Text></Pressable>
         </View>}
       </View>)}
       {!linhas.length&&<Text style={s.note}>Nenhuma linha encontrada. Tente outro termo.</Text>}
       </>}
       {painel==="tarifas"&&<View style={s.info}>
         <Text style={s.title}>Tarifas e integrações</Text>
         <Text style={s.note}>Vigência de referência: 06/01/2026. Consulta das fontes: 17/11/2026. Tarifa comum não depende da distância nem da estação. Transferências podem exigir pagamento fora das áreas ou horários gratuitos.</Text>
         {TABELA_TARIFAS.map(([nome,valor])=><View key={nome} style={s.station}><Text style={[s.stationName,{flex:1}]}>{nome}</Text><Text style={s.fare}>{valor}</Text></View>)}
         <Text style={s.note}>Linhas 6 e 17: operação especial gratuita enquanto vigente. Tatuapé e Corinthians-Itaquera: segunda a sexta, 10h–17h e 20h–24h; sábados, domingos e feriados durante operação comercial.</Text>
         <Pressable onPress={()=>abrir(TARIFAS)} accessibilityRole="link"><Text style={s.link}>Tarifas oficiais do Metrô ↗</Text></Pressable>
         <Pressable onPress={()=>abrir(TARIFAS_SPTRANS)} accessibilityRole="link"><Text style={s.link}>Tarifas de integração SPTrans ↗</Text></Pressable>
       </View>}
       <View style={s.info}>
         <Text style={s.title}>Informações úteis</Text>
         <Pressable onPress={()=>abrir(HORARIOS)} style={s.infoLink}><Ionicons name="time-outline" size={19} color="#0071e3"/><Text style={s.link}>Horários do Metrô</Text></Pressable>
         <Pressable onPress={()=>abrir(ESTADO)} style={s.infoLink}><Ionicons name="pulse-outline" size={19} color="#0071e3"/><Text style={s.link}>Situação das linhas do Metrô</Text></Pressable>
         <Text style={s.note}>Consulte cada operador para informações atualizadas, tarifas, interrupções e disponibilidade de elevadores. A lista não confirma operação nem acessibilidade em tempo real.</Text>
       </View>
       {!!erro&&<Text style={s.note} accessibilityRole="alert">{erro}</Text>}
       </ScrollView>
     </View>
   </View>
 </View>;
}

const s=StyleSheet.create({
 page:{gap:18,paddingTop:24,paddingBottom:24},
 intro:{gap:7},
 eyebrow:{fontSize:11,fontWeight:"600",letterSpacing:1.4,color:"#0069d2"},
 heading:{fontSize:30,fontWeight:"600",letterSpacing:-.8,color:"#1d2633"},
 subtitle:{fontSize:14,lineHeight:21,color:"#586c80"},
 layout:{flexDirection:"row",alignItems:"stretch",gap:14},
 layoutMobile:{flexDirection:"column",alignItems:"stretch"},
 mapCard:{flex:1,minWidth:0,minHeight:0,backgroundColor:"#fff",borderRadius:20,borderWidth:1,borderColor:"#d9e6f5",padding:14,gap:12},
 mapMobile:{flex:0,width:"100%"},
 details:{width:360,minHeight:0,flexShrink:0,backgroundColor:"#fff",borderWidth:1,borderColor:"#d9e6f5",borderRadius:20,padding:14,gap:8},
 detailsMobile:{width:"100%"},
 header:{flexShrink:0,minHeight:52,flexDirection:"row",justifyContent:"space-between",alignItems:"center",gap:10,borderBottomWidth:1,borderBottomColor:"#e4edf5",paddingBottom:12},
 title:{fontSize:17,fontWeight:"600",color:"#1d2633"},
 small:{fontSize:12,color:"#64748b",lineHeight:18},
 primary:{flexDirection:"row",alignItems:"center",gap:6,paddingHorizontal:12,paddingVertical:10,borderRadius:10,backgroundColor:"#0071e3"},
 primaryText:{fontSize:12,color:"#fff",fontWeight:"600"},
 nativePreview:{minHeight:240,backgroundColor:"#f2f7fc",borderRadius:14,alignItems:"center",justifyContent:"center",padding:20,gap:12},
 note:{fontSize:11,color:"#64748b",lineHeight:17},
 link:{fontSize:12,fontWeight:"500",color:"#0069d2",lineHeight:19},
 search:{flexDirection:"row",alignItems:"center",backgroundColor:"#f0f5fa",borderRadius:10,paddingHorizontal:10,gap:7},
 input:{flex:1,minWidth:0,paddingVertical:12,fontSize:12,color:"#1d2633"},
 filters:{flexDirection:"row",flexWrap:"wrap",gap:5,paddingVertical:4},
 filter:{paddingHorizontal:9,paddingVertical:7,borderRadius:9,backgroundColor:"#f0f5fa"},
 active:{backgroundColor:"#dcebfa"},
 filterText:{fontSize:11,color:"#64748b"},
 activeText:{color:"#0069d2",fontWeight:"600"},
 mapTools:{flexDirection:"row",alignItems:"center",justifyContent:"space-between",gap:6,flexWrap:"wrap"},
 zoomGroup:{flexDirection:"row",gap:5,alignItems:"center"},
 zoomButton:{minWidth:34,minHeight:34,paddingHorizontal:8,backgroundColor:"#edf3f9",borderRadius:8,alignItems:"center",justifyContent:"center"},
 mapViewport:{flex:1,minHeight:0,borderRadius:12,overflow:"hidden",backgroundColor:"#f3f7fb",borderWidth:1,borderColor:"#e4edf5"},
 mapViewportMobile:{flex:0,height:520},
 sectionTabs:{flexDirection:"row",backgroundColor:"#edf3f9",borderRadius:11,padding:3,gap:3},
 sectionTab:{flex:1,alignItems:"center",justifyContent:"center",minHeight:34,borderRadius:9},
 sectionTabActive:{backgroundColor:"#fff"},
 lineScroll:{flex:1,minHeight:0},
 lineScrollContent:{paddingRight:5,paddingBottom:12},
 lineGroup:{borderBottomWidth:1,borderBottomColor:"#eaf0f6"},
 line:{flexDirection:"row",alignItems:"center",gap:8,minHeight:63,paddingVertical:9},
 lineLabel:{flex:1,minWidth:0},
 fare:{fontSize:12,fontWeight:"600",color:"#1d2633",flexShrink:0},
 expanded:{marginLeft:8,padding:10,backgroundColor:"#f5f8fc",borderRadius:10,gap:7,marginBottom:8},
 station:{flexDirection:"row",alignItems:"center",gap:8,borderBottomWidth:1,borderBottomColor:"#e1eaf4",paddingVertical:7},
 stationName:{fontSize:12,color:"#344b62",lineHeight:18},
 number:{width:34,height:30,borderRadius:8,alignItems:"center",justifyContent:"center"},
 numberText:{fontSize:14,fontWeight:"600",color:"#fff"},
 lineName:{fontSize:13,fontWeight:"600",color:"#1d2633",lineHeight:18},
 extremos:{fontSize:12,lineHeight:18,color:"#41566c"},
 info:{gap:10,marginTop:8,padding:12,borderRadius:12,backgroundColor:"#f3f7fb"},
 infoLink:{flexDirection:"row",alignItems:"center",gap:8},
});
