import React,{useRef} from "react";
import {Image,Pressable,ScrollView,StyleSheet,Text,View,useWindowDimensions} from "react-native";
import {Ionicons} from "@expo/vector-icons";

const recursos=[
 {icone:"navigate-outline",titulo:"Mobilidade inteligente",descricao:"Planeje trajetos combinando ônibus, metrô, trens e caminhadas."},
 {icone:"location-outline",titulo:"Mais autonomia",descricao:"Acompanhe a viagem com GPS e orientações de embarque e desembarque."},
 {icone:"wallet-outline",titulo:"Economia no percurso",descricao:"Compare alternativas e estimativas de custos de transporte."},
 {icone:"chatbubble-ellipses-outline",titulo:"Informação acessível",descricao:"Consulte orientações sobre transporte público com referências institucionais."}
] as const;

export default function TelaInicial({abrir}:{abrir:()=>void}){
 const {width,height}=useWindowDimensions();
 const mobile=width<850;
 const scroll=useRef<ScrollView>(null);
 const sobreY=useRef(0);
 const recursosY=useRef(0);
 const ir=(y:number)=>scroll.current?.scrollTo({y,animated:true});
 return <ScrollView ref={scroll} style={s.page} contentContainerStyle={{flexGrow:1}}>
   <View style={s.header}><View style={[s.headerInner,mobile&&s.headerMobile]}>
     <Pressable accessibilityRole="button" onPress={()=>ir(0)} style={s.brand}><View style={s.logo}><Ionicons name="navigate" size={23} color="#fff"/></View><View><Text style={s.brandText}>Citizen Tech</Text><Text style={s.brandSub}>MOBILIDADE URBANA</Text></View></Pressable>
     <View style={[s.headerActions,mobile&&s.headerActionsMobile]}>
       <Pressable style={s.navButton} accessibilityRole="button" onPress={()=>ir(sobreY.current)}><Text style={s.navText}>Sobre</Text></Pressable>
       <Pressable style={s.navButton} accessibilityRole="button" onPress={()=>ir(recursosY.current)}><Text style={s.navText}>Recursos</Text></Pressable>
       <Pressable style={s.headerCta} accessibilityRole="button" onPress={abrir}><Text style={s.headerCtaText}>Acessar projeto</Text><Ionicons name="arrow-forward" size={17} color="#fff"/></Pressable>
     </View>
   </View></View>
   <View style={[s.hero,{minHeight:mobile?0:Math.max(600,height-88)},mobile&&s.heroMobile]}>
     <View style={[s.heroInner,mobile&&s.heroInnerMobile]}>
       <View style={[s.copy,mobile&&s.copyMobile]}>
         <Text style={s.eyebrow}>CITIZEN TECH · GLOBAL SOLUTION 2026</Text>
         <Text accessibilityRole="header" style={[s.heading,mobile&&s.headingMobile]}>O futuro da{"\n"}mobilidade{"\n"}<Text style={s.accent}>é para todos.</Text></Text>
         <Text style={s.description}>Tecnologia que conecta pessoas à cidade. Transforme o jeito de se deslocar por São Paulo, com mais autonomia, informação e economia.</Text>
         <Pressable accessibilityRole="button" onPress={abrir} style={({pressed})=>[s.primary,pressed&&s.pressed]}><Text style={s.primaryText}>Explorar o projeto</Text><Ionicons name="arrow-forward" size={22} color="#fff"/></Pressable>
         <View style={s.location}><Ionicons name="location-outline" size={17} color="#526f91"/><Text style={s.caption}>São Paulo · Brasil</Text></View>
       </View>
       <View style={[s.visual,mobile&&s.visualMobile]}>
         <Image source={require("../assets/metro_futurista.jpg")} style={s.image} resizeMode="cover" accessibilityLabel="Metrô futurista em uma cidade conectada"/>
         <View style={s.imageShade}/>
         <View style={s.visualBottom}><Text style={s.visualTitle}>Conectando pessoas.</Text><Text style={s.visualSubtitle}>Transformando caminhos.</Text><View style={s.transport}><Ionicons name="train-outline" size={23} color="#fff"/><View style={s.connector}/><Ionicons name="bus-outline" size={23} color="#fff"/><View style={s.connector}/><Ionicons name="walk-outline" size={23} color="#fff"/></View></View>
       </View>
     </View>
   </View>
   <View onLayout={e=>sobreY.current=e.nativeEvent.layout.y} style={s.section}><View style={[s.sectionInner,mobile&&s.sectionMobile]}><Text style={s.eyebrow}>NOSSO PROPÓSITO</Text><Text style={[s.sectionTitle,mobile&&s.sectionTitleMobile]}>Uma cidade mais conectada começa pelas pessoas.</Text><Text style={s.sectionText}>O Citizen Tech é um projeto acadêmico da FIAP que aproxima o cidadão das informações e opções de mobilidade urbana. Reunimos planejamento de trajetos, horários de transporte, acompanhamento de viagens e orientação ao cidadão em uma única plataforma.</Text></View></View>
   <View onLayout={e=>recursosY.current=e.nativeEvent.layout.y} style={s.resources}><View style={[s.sectionInner,mobile&&s.sectionMobile]}><Text style={s.eyebrow}>O QUE CONSTRUÍMOS</Text><Text style={[s.sectionTitle,mobile&&s.sectionTitleMobile]}>Mais do que chegar ao destino.</Text><View style={[s.grid,mobile&&s.gridMobile]}>{recursos.map(r=><View key={r.titulo} style={[s.card,mobile&&s.cardMobile]}><View style={s.icon}><Ionicons name={r.icone} size={26} color="#0069d2"/></View><Text style={s.cardTitle}>{r.titulo}</Text><Text style={s.caption}>{r.descricao}</Text></View>)}</View></View></View>
   <View style={s.final}><Text style={s.finalTitle}>O próximo caminho é seu.</Text><Pressable onPress={abrir} accessibilityRole="button" style={[s.primary,{alignSelf:"center"}]}><Text style={s.primaryText}>Acessar Citizen Tech</Text><Ionicons name="arrow-forward" size={20} color="#fff"/></Pressable><Text style={s.disclaimer}>Protótipo acadêmico. Não representa um serviço oficial de transporte.</Text></View>
   <View style={s.footer}><Text style={s.caption}>Citizen Tech Mobilidade Urbana · FIAP · Global Solution 2026</Text></View>
 </ScrollView>;
}
const s=StyleSheet.create({
 page:{flex:1,backgroundColor:"#fff"},
 header:{backgroundColor:"#fff",borderBottomWidth:1,borderBottomColor:"#e1ebf5"},
 headerInner:{width:"100%",maxWidth:1440,alignSelf:"center",minHeight:84,paddingHorizontal:48,paddingVertical:14,flexDirection:"row",alignItems:"center",justifyContent:"space-between",gap:14},
 headerMobile:{paddingHorizontal:20,flexWrap:"wrap"},
 brand:{flexDirection:"row",alignItems:"center",gap:11,minHeight:48},
 logo:{width:43,height:43,borderRadius:13,backgroundColor:"#0071e3",justifyContent:"center",alignItems:"center"},
 brandText:{fontSize:23,fontWeight:"700",color:"#162c49",letterSpacing:-.7},brandSub:{fontSize:9,letterSpacing:1.3,color:"#55769a",fontWeight:"600"},
 headerActions:{flexDirection:"row",gap:8,alignItems:"center",flexWrap:"wrap"},headerActionsMobile:{width:"100%"},
 navButton:{minHeight:44,paddingHorizontal:14,justifyContent:"center",borderWidth:1,borderColor:"#dce7f2",borderRadius:10},navText:{fontSize:13,color:"#34516e",fontWeight:"600"},
 headerCta:{minHeight:44,paddingHorizontal:15,backgroundColor:"#0071e3",borderRadius:10,flexDirection:"row",alignItems:"center",justifyContent:"center",gap:8},headerCtaText:{color:"#fff",fontSize:13,fontWeight:"700"},
 hero:{backgroundColor:"#eef6ff",justifyContent:"center"},heroMobile:{paddingVertical:12},
 heroInner:{flexDirection:"row",width:"100%",maxWidth:1440,alignSelf:"center",padding:48,gap:48,alignItems:"center"},heroInnerMobile:{flexDirection:"column",padding:20,gap:25,alignItems:"stretch"},
 copy:{flex:1,minWidth:0,gap:22},copyMobile:{flex:0,gap:16},
 eyebrow:{color:"#0069d2",fontSize:11,fontWeight:"700",letterSpacing:1.8},
 heading:{fontSize:64,lineHeight:70,fontWeight:"700",letterSpacing:-2.9,color:"#162c49"},headingMobile:{fontSize:43,lineHeight:49,letterSpacing:-1.6},accent:{color:"#0069d2"},
 description:{fontSize:17,lineHeight:26,color:"#52677e",maxWidth:480},
 primary:{minHeight:56,backgroundColor:"#0071e3",paddingHorizontal:22,paddingVertical:14,borderRadius:12,flexDirection:"row",alignItems:"center",justifyContent:"center",gap:15,alignSelf:"flex-start"},primaryText:{fontSize:16,fontWeight:"700",color:"#fff"},pressed:{opacity:.8},
 location:{flexDirection:"row",alignItems:"center",gap:6},caption:{fontSize:13,color:"#60768f",lineHeight:20},
 visual:{flex:1.15,height:490,borderRadius:24,overflow:"hidden",backgroundColor:"#173459"},visualMobile:{flex:0,height:285},
 image:{position:"absolute",width:"100%",height:"100%"},imageShade:{position:"absolute",top:0,left:0,right:0,bottom:0,backgroundColor:"rgba(10,34,67,.19)"},
 visualBottom:{position:"absolute",left:0,right:0,bottom:0,padding:24,backgroundColor:"rgba(9,26,52,.85)",gap:7},visualTitle:{fontSize:23,fontWeight:"700",color:"#fff"},visualSubtitle:{color:"#c5e3ff",fontSize:15},transport:{flexDirection:"row",alignItems:"center",gap:10,marginTop:6},connector:{height:2,width:24,backgroundColor:"#64d9fe"},
 section:{backgroundColor:"#fff"},sectionInner:{maxWidth:1440,width:"100%",alignSelf:"center",paddingHorizontal:48,paddingVertical:62,gap:17},sectionMobile:{paddingHorizontal:20,paddingVertical:36},
 sectionTitle:{fontSize:37,fontWeight:"700",color:"#162c49",letterSpacing:-.9,maxWidth:800},sectionTitleMobile:{fontSize:29},sectionText:{maxWidth:900,fontSize:16,color:"#52677e",lineHeight:26},
 resources:{backgroundColor:"#f4f8fd"},grid:{flexDirection:"row",gap:14,flexWrap:"wrap",marginTop:12},gridMobile:{flexDirection:"column"},card:{flex:1,minWidth:220,minHeight:174,padding:20,borderRadius:16,backgroundColor:"#fff",borderWidth:1,borderColor:"#d9e7f5",gap:12},cardMobile:{flex:0,minHeight:0},icon:{width:48,height:48,borderRadius:12,backgroundColor:"#e8f3ff",alignItems:"center",justifyContent:"center"},cardTitle:{fontSize:17,fontWeight:"700",color:"#203957"},
 final:{backgroundColor:"#e8f3ff",padding:36,alignItems:"center",gap:20},finalTitle:{fontSize:28,fontWeight:"700",color:"#162c49",textAlign:"center"},disclaimer:{fontSize:12,color:"#60768f",textAlign:"center"},footer:{padding:22,alignItems:"center"}
});
