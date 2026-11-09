import React, { useState } from "react";
import { View, Text, TextInput, TouchableOpacity, ScrollView, StyleSheet, ActivityIndicator } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const API = process.env.EXPO_PUBLIC_API_URL || "http://127.0.0.1:8000";
type Retorno = { status:string; resposta:string; fontes:{referencia:string;data_verificacao:string}[]; relacionados:string[] };
const categorias = ["Cartões", "Gratuidade", "Acessibilidade", "Direitos"];

export default function Home() {
  const [pergunta, setPergunta] = useState("");
  const [resultado, setResultado] = useState<Retorno|null>(null);
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(false);
  async function consultar(texto:string) {
    setPergunta(texto); setResultado(null); setErro(""); setCarregando(true);
    try {
      const r = await fetch(API + "/consultar", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({pergunta:texto,modelo:"B"})});
      if (!r.ok) throw new Error("API indisponível");
      setResultado(await r.json());
    } catch {
      setErro("Não foi possível consultar. Verifique se o servidor Python está ligado e configurado.");
    } finally {setCarregando(false);}
  }
  return <ScrollView contentContainerStyle={s.page}><View style={s.shell}>
    <View style={s.brand}><Ionicons name="bus-outline" size={26} color="#6578b6"/><Text style={s.brandText}>Citizen Mobilidade</Text></View>
    <Text style={s.title}>Sua cidade, mais acessível.</Text>
    <Text style={s.subtitle}>Um jeito simples de encontrar informações sobre transporte e seus direitos.</Text>
    <View style={s.search}><Ionicons name="search-outline" size={23} color="#6578b6"/><TextInput value={pergunta} onChangeText={setPergunta} onSubmitEditing={()=>consultar(pergunta)} placeholder="Como podemos ajudar?" placeholderTextColor="#7785a7" style={s.input} accessibilityLabel="Digite sua pergunta"/><TouchableOpacity onPress={()=>consultar(pergunta)} accessibilityLabel="Buscar"><Ionicons name="arrow-forward-circle" size={30} color="#6578b6"/></TouchableOpacity></View>
    <Text style={s.heading}>Explore por assunto</Text>
    <View style={s.grid}>{categorias.map((nome,i)=><TouchableOpacity key={nome} style={s.card} onPress={()=>consultar(nome)}><Ionicons name={(["card-outline","people-outline","accessibility-outline","shield-checkmark-outline"] as const)[i]} color="#6174b1" size={29}/><Text style={s.cardText}>{nome}</Text></TouchableOpacity>)}</View>
    <View style={s.panel}><Text style={s.heading}>Assistente cidadão</Text><Text style={s.copy}>Respostas com referências verificadas. Projeto acadêmico, não oficial.</Text>{carregando && <ActivityIndicator color="#6578b6"/>}{erro!=="" && <Text style={s.error}>{erro}</Text>}{resultado && <><Text style={s.copy}>{resultado.resposta}</Text>{resultado.fontes.map((f,i)=><Text key={i} style={s.copy}>Fonte: {f.referencia} · {f.data_verificacao}</Text>)}{resultado.relacionados.length>0 && <Text style={s.copy}>Explore: {resultado.relacionados.join(", ")}</Text>}</>}</View>
    <Text style={s.footer}>FIAP · Global Solution 2026</Text>
  </View></ScrollView>;
}
const s=StyleSheet.create({
  page:{flexGrow:1,backgroundColor:"#dce6fb",alignItems:"center",padding:20},
  shell:{width:"100%",maxWidth:720,backgroundColor:"#eef2fe",borderRadius:30,padding:25,minHeight:730},
  brand:{flexDirection:"row",gap:10,alignItems:"center",marginBottom:40},
  brandText:{color:"#465a8a",fontSize:19,fontWeight:"700"},
  title:{color:"#29385c",fontSize:35,fontWeight:"700",lineHeight:43,maxWidth:460},
  subtitle:{color:"#596b91",fontSize:16,lineHeight:25,marginTop:12},
  search:{flexDirection:"row",alignItems:"center",gap:10,backgroundColor:"#fff",padding:14,borderRadius:23,marginTop:25},
  input:{flex:1,fontSize:16,color:"#29385c",minHeight:36},
  heading:{fontWeight:"700",fontSize:20,color:"#2e426e",marginBottom:12,marginTop:24},
  grid:{flexDirection:"row",flexWrap:"wrap",gap:12},
  card:{flexGrow:1,width:"46%",minHeight:110,backgroundColor:"#fff",borderRadius:23,alignItems:"center",justifyContent:"center",gap:9,padding:10},
  cardText:{color:"#374a78",fontSize:15,fontWeight:"600"},
  panel:{backgroundColor:"#fff",borderRadius:24,padding:20,marginTop:25},
  copy:{fontSize:15,color:"#58698c",lineHeight:24,marginBottom:8},
  error:{fontSize:14,color:"#b3475a"},
  footer:{color:"#7180a2",fontSize:12,textAlign:"center",marginTop:25}
});
