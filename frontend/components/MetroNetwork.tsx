import React, { useState } from "react";
import { Linking, Platform, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const PAGINA_MAPA = "https://www.metro.sp.gov.br/sua-viagem/mapa-da-rede/";
const PDF_MAPA = "https://www.metro.sp.gov.br/wp-content/uploads/2026/07/mapa-da-rede.pdf";
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
 {numero:"6",nome:"Laranja",cor:"#F47920",operador:"Linha Uni",extremos:"Brasilândia · São Joaquim (consulte o operador sobre a implantação)",tipo:"metro"},
 {numero:"7",nome:"Rubi",cor:"#A6192E",operador:"TIC Trens",extremos:"Palmeiras-Barra Funda · Jundiaí",tipo:"trem"},
 {numero:"8",nome:"Diamante",cor:"#8F9498",operador:"Motiva",extremos:"Júlio Prestes · Itapevi",tipo:"trem"},
 {numero:"9",nome:"Esmeralda",cor:"#008A72",operador:"Motiva",extremos:"Osasco · Varginha",tipo:"trem"},
 {numero:"10",nome:"Turquesa",cor:"#008F95",operador:"CPTM",extremos:"Brás · Rio Grande da Serra",tipo:"trem"},
 {numero:"11",nome:"Coral",cor:"#F36C38",operador:"Trivia",extremos:"Palmeiras-Barra Funda · Estudantes",tipo:"trem"},
 {numero:"12",nome:"Safira",cor:"#153E84",operador:"Trivia",extremos:"Brás · Calmon Viana",tipo:"trem"},
 {numero:"13",nome:"Jade",cor:"#00A5A5",operador:"Trivia",extremos:"Eng. Goulart · Aeroporto-Guarulhos",tipo:"trem"},
 {numero:"15",nome:"Prata",cor:"#8C98A3",operador:"Metrô",extremos:"Vila Prudente · Jardim Colonial",tipo:"monotrilho"},
 {numero:"17",nome:"Ouro",cor:"#B89035",operador:"Metrô",extremos:"Morumbi · Aeroporto de Congonhas",tipo:"monotrilho"},
];
type Filtro = "todos" | Linha["tipo"];
const filtros: {id:Filtro;label:string}[] = [{id:"todos",label:"Todas"},{id:"metro",label:"Metrô"},{id:"trem",label:"Trem"},{id:"monotrilho",label:"Monotrilho"}];
const normalizar=(s:string)=>s.normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase();

export default function MetroNetwork({mobile}:{mobile:boolean}){
 const [filtro,setFiltro]=useState<Filtro>("todos");
 const [busca,setBusca]=useState("");
 const [selecionada,setSelecionada]=useState<string|null>(null);
 const [erro,setErro]=useState("");
 const abrir=async(url:string)=>{
   setErro("");
   try{await Linking.openURL(url);}catch{setErro("Não foi possível abrir o site oficial. Tente novamente.");}
 };
 const linhas=LINHAS.filter(l=>(filtro==="todos"||l.tipo===filtro)&&normalizar(l.numero+" "+l.nome+" "+l.operador+" "+l.extremos).includes(normalizar(busca.trim())));
 return <View style={s.page}>
   <View style={s.intro}>
     <Text style={s.eyebrow}>REDE METROPOLITANA · SÃO PAULO</Text>
     <Text style={s.heading}>Explore a rede de metrô e trens.</Text>
     <Text style={s.subtitle}>Consulte as linhas, integrações e estações no mapa oficial antes de planejar sua viagem.</Text>
   </View>
   <View style={[s.layout,mobile&&s.layoutMobile]}>
     <View style={[s.mapCard,mobile&&s.mapMobile]}>
       <View style={s.header}><View style={{flex:1}}><Text style={s.title}>Mapa da rede</Text><Text style={s.small}>Documento oficial · julho de 2026</Text></View><Pressable onPress={()=>abrir(PDF_MAPA)} style={s.primary} accessibilityRole="button"><Ionicons name="expand-outline" size={16} color="#fff"/><Text style={s.primaryText}>Abrir PDF</Text></Pressable></View>
       {Platform.OS==="web"?React.createElement("iframe",{title:"Mapa oficial do transporte metropolitano de São Paulo",src:PDF_MAPA+"#view=FitH",style:{display:"block",width:"100%",height:mobile?490:720,border:0,borderRadius:12,background:"#f2f5f8"}}):<View style={s.nativePreview}><Ionicons name="map-outline" color="#0071e3" size={48}/><Text style={s.title}>Mapa completo da rede</Text><Text style={s.small}>Abra o PDF oficial para ampliar e consultar as estações no seu aparelho.</Text><Pressable onPress={()=>abrir(PDF_MAPA)} style={s.primary}><Text style={s.primaryText}>Visualizar mapa</Text></Pressable></View>}
       <Text style={s.note}>Fonte: Companhia do Metropolitano de São Paulo. O mapa é esquemático: não representa distâncias reais. Caso a visualização não carregue, use Abrir PDF.</Text>
       <Pressable onPress={()=>abrir(PAGINA_MAPA)} accessibilityRole="link"><Text style={s.link}>Consultar a versão mais recente no site oficial ↗</Text></Pressable>
     </View>
     <View style={[s.details,mobile&&s.detailsMobile]}>
       <View style={s.header}><Text style={s.title}>Linhas da rede</Text><Text style={s.small}>{linhas.length} linhas</Text></View>
       <View style={s.search}><Ionicons name="search-outline" size={17} color="#64748b"/><TextInput value={busca} onChangeText={setBusca} placeholder="Buscar linha, estação terminal..." placeholderTextColor="#8898a8" style={s.input} accessibilityLabel="Buscar linhas ferroviárias"/></View>
       <View style={s.filters}>{filtros.map(f=><Pressable key={f.id} onPress={()=>setFiltro(f.id)} style={[s.filter,filtro===f.id&&s.active]} accessibilityRole="button" accessibilityState={{selected:filtro===f.id}}><Text style={[s.filterText,filtro===f.id&&s.activeText]}>{f.label}</Text></Pressable>)}</View>
       {linhas.map(l=><Pressable key={l.numero} onPress={()=>setSelecionada(x=>x===l.numero?null:l.numero)} style={s.line} accessibilityRole="button" accessibilityState={{expanded:selecionada===l.numero}}>
         <View style={[s.number,{backgroundColor:l.cor}]}><Text style={[s.numberText,["4","8","15","17"].includes(l.numero)&&{color:"#172333"}]}>{l.numero}</Text></View>
         <View style={{flex:1,minWidth:0}}><Text style={s.lineName}>Linha {l.numero} – {l.nome}</Text><Text style={s.small}>{l.operador}</Text>{selecionada===l.numero&&<View style={{marginTop:7,gap:5}}><Text style={s.extremos}>{l.extremos}</Text><Pressable onPress={()=>abrir(OPERADORES[l.operador])} accessibilityRole="link"><Text style={s.link}>Informações no operador ↗</Text></Pressable></View>}</View>
         <Ionicons name={selecionada===l.numero?"chevron-up":"chevron-down"} size={16} color="#8797a7"/>
       </Pressable>)}
       {!linhas.length&&<Text style={s.note}>Nenhuma linha encontrada. Tente outro termo.</Text>}
       <View style={s.info}>
         <Text style={s.title}>Informações úteis</Text>
         <Pressable onPress={()=>abrir(HORARIOS)} style={s.infoLink}><Ionicons name="time-outline" size={19} color="#0071e3"/><Text style={s.link}>Horários do Metrô</Text></Pressable>
         <Pressable onPress={()=>abrir(ESTADO)} style={s.infoLink}><Ionicons name="pulse-outline" size={19} color="#0071e3"/><Text style={s.link}>Situação das linhas do Metrô</Text></Pressable>
         <Text style={s.note}>Consulte cada operador para informações atualizadas, tarifas, interrupções e disponibilidade de elevadores. A lista não confirma operação nem acessibilidade em tempo real.</Text>
       </View>
       {!!erro&&<Text style={s.note} accessibilityRole="alert">{erro}</Text>}
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
 layout:{flexDirection:"row",alignItems:"flex-start",gap:14},
 layoutMobile:{flexDirection:"column",alignItems:"stretch"},
 mapCard:{flex:1,minWidth:0,backgroundColor:"#fff",borderRadius:20,borderWidth:1,borderColor:"#d9e6f5",padding:14,gap:12},
 mapMobile:{flex:0,width:"100%"},
 details:{width:324,backgroundColor:"#fff",borderWidth:1,borderColor:"#d9e6f5",borderRadius:20,padding:14,gap:8},
 detailsMobile:{width:"100%"},
 header:{flexDirection:"row",justifyContent:"space-between",alignItems:"center",gap:10,borderBottomWidth:1,borderBottomColor:"#e4edf5",paddingBottom:12},
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
 line:{flexDirection:"row",alignItems:"flex-start",gap:9,paddingVertical:10,borderBottomWidth:1,borderBottomColor:"#eaf0f6"},
 number:{width:34,height:30,borderRadius:8,alignItems:"center",justifyContent:"center"},
 numberText:{fontSize:14,fontWeight:"600",color:"#fff"},
 lineName:{fontSize:13,fontWeight:"600",color:"#1d2633",lineHeight:18},
 extremos:{fontSize:12,lineHeight:18,color:"#41566c"},
 info:{gap:10,marginTop:8,padding:12,borderRadius:12,backgroundColor:"#f3f7fb"},
 infoLink:{flexDirection:"row",alignItems:"center",gap:8},
});
