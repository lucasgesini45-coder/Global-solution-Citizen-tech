import React from "react";
import {Image, Pressable, StyleSheet, Text, View, useWindowDimensions} from "react-native";
import {Ionicons} from "@expo/vector-icons";

type Destino = "planejar" | "metro" | "horarios" | "viagem" | "economia";
const recursos: {titulo:string;descricao:string;icone:React.ComponentProps<typeof Ionicons>["name"];destino:Destino}[] = [
 {titulo:"Planejar trajeto",descricao:"Encontre seu caminho pela cidade.",icone:"navigate-outline",destino:"planejar"},
 {titulo:"Viajar com autonomia",descricao:"Acompanhe cada etapa da viagem.",icone:"locate-outline",destino:"viagem"},
 {titulo:"Economizar",descricao:"Compare opções e custos.",icone:"wallet-outline",destino:"economia"},
];

export default function TelaInicial({abrir}:{abrir:(destino:Destino)=>void}){
 const {width}=useWindowDimensions();
 const compacto=width<900;
 return <View style={s.page}>
   <View style={[s.hero,compacto&&s.heroMobile]}>
     <View style={[s.copy,compacto&&s.copyMobile]}>
       <View style={s.eyebrowRow}><View style={s.dot}/><Text style={s.eyebrow}>CIDADANIA EM MOVIMENTO</Text></View>
       <Text accessibilityRole="header" style={[s.heading,compacto&&s.headingMobile]}>Sua cidade.{"\n"}Seu caminho.{"\n"}<Text style={s.accent}>Sua liberdade.</Text></Text>
       <Text style={s.description}>Uma forma mais inteligente de se mover por São Paulo. Planeje, economize e viaje com mais autonomia.</Text>
       <Pressable onPress={()=>abrir("planejar")} accessibilityRole="button" style={({pressed})=>[s.primary,pressed&&s.pressed]}>
         <Text style={s.primaryText}>Começar minha viagem</Text><Ionicons name="arrow-forward" size={21} color="#fff"/>
       </Pressable>
       <View style={s.location}><Ionicons name="location-outline" size={16} color="#526f91"/><Text style={s.caption}>São Paulo, Brasil</Text></View>
     </View>
     <View style={[s.visual,compacto&&s.visualMobile]}>
       <Image source={require("../assets/metro_futurista.jpg")} resizeMode="cover" style={s.image} accessibilityLabel="Metrô futurista iluminado em azul, representando mobilidade inteligente"/>
       <View style={s.imageLabel}><View style={s.signal}/><Text style={s.imageLabelText}>MOBILIDADE INTELIGENTE</Text></View>
       <View style={s.imageFooter}><Ionicons name="train-outline" size={21} color="#fff"/><View style={s.connector}/><Ionicons name="bus-outline" size={21} color="#fff"/><View style={s.connector}/><Ionicons name="walk-outline" size={21} color="#fff"/></View>
     </View>
   </View>
   <View style={s.section}>
     <Text style={s.sectionTitle}>A cidade ao seu alcance.</Text>
     <View style={[s.cards,compacto&&s.cardsMobile]}>{recursos.map(r=><Pressable key={r.destino} onPress={()=>abrir(r.destino)} accessibilityRole="button" style={({pressed})=>[s.card,compacto&&s.cardMobile,pressed&&s.pressed]}>
       <View style={s.icon}><Ionicons name={r.icone} size={24} color="#0069d2"/></View><View style={{flex:1}}><Text style={s.cardTitle}>{r.titulo}</Text><Text style={s.caption}>{r.descricao}</Text></View><Ionicons name="arrow-forward-outline" size={19} color="#0069d2"/>
     </Pressable>)}</View>
   </View>
 </View>;
}
const s=StyleSheet.create({
 page:{paddingTop:25,paddingBottom:12,gap:24},
 hero:{flexDirection:"row",backgroundColor:"#fff",borderRadius:26,borderWidth:1,borderColor:"#d4e4f5",overflow:"hidden",minHeight:470},
 heroMobile:{flexDirection:"column",minHeight:0},
 copy:{flex:1,padding:40,justifyContent:"center",gap:20,minWidth:0},
 copyMobile:{padding:24,gap:16},
 eyebrowRow:{flexDirection:"row",alignItems:"center",gap:8},
 dot:{width:8,height:8,borderRadius:4,backgroundColor:"#0071e3"},
 eyebrow:{fontSize:11,letterSpacing:1.5,color:"#0069d2",fontWeight:"700"},
 heading:{fontSize:51,lineHeight:58,letterSpacing:-2.1,fontWeight:"700",color:"#162c49"},
 headingMobile:{fontSize:38,lineHeight:45,letterSpacing:-1.4},
 accent:{color:"#0069d2"},
 description:{fontSize:16,lineHeight:24,color:"#586c80",maxWidth:420},
 primary:{backgroundColor:"#0071e3",borderRadius:13,minHeight:54,paddingHorizontal:20,paddingVertical:12,flexDirection:"row",alignItems:"center",justifyContent:"center",gap:12,alignSelf:"flex-start"},
 primaryText:{fontSize:15,color:"#fff",fontWeight:"700"},
 pressed:{opacity:.8},
 location:{flexDirection:"row",alignItems:"center",gap:6},
 caption:{fontSize:12,lineHeight:18,color:"#60768f"},
 visual:{flex:1.2,position:"relative",minHeight:470,backgroundColor:"#173459"},
 visualMobile:{flex:0,minHeight:260,height:260},
 image:{position:"absolute",width:"100%",height:"100%"},
 imageLabel:{position:"absolute",top:18,left:18,right:18,flexDirection:"row",alignSelf:"flex-start",alignItems:"center",gap:8,backgroundColor:"rgba(9,30,61,.82)",padding:12,borderRadius:10},
 signal:{width:7,height:7,borderRadius:4,backgroundColor:"#55dafc"},
 imageLabelText:{color:"#fff",fontSize:10,fontWeight:"700",letterSpacing:1},
 imageFooter:{position:"absolute",bottom:18,left:18,backgroundColor:"rgba(9,30,61,.86)",borderRadius:12,padding:12,flexDirection:"row",alignItems:"center",gap:9},
 connector:{height:2,width:20,backgroundColor:"#61d9fa"},
 section:{gap:13},
 sectionTitle:{fontSize:21,fontWeight:"600",color:"#1d2633"},
 cards:{flexDirection:"row",gap:12},
 cardsMobile:{flexDirection:"column"},
 card:{flex:1,minHeight:100,padding:16,flexDirection:"row",alignItems:"center",gap:12,backgroundColor:"#fff",borderRadius:16,borderWidth:1,borderColor:"#c4d9ee"},
 cardMobile:{flex:0},
 icon:{height:46,width:46,borderRadius:12,backgroundColor:"#e8f3ff",alignItems:"center",justifyContent:"center"},
 cardTitle:{fontSize:14,fontWeight:"700",color:"#203957",marginBottom:4}
});
