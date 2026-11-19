import React,{useRef} from "react";
import {Image,Platform,Pressable,ScrollView,StyleSheet,Text,View,useWindowDimensions,type ViewStyle} from "react-native";
import {Ionicons} from "@expo/vector-icons";
import heroImage from "./heroImage";

const recursos=[
 {icone:"git-compare-outline",titulo:"Planejamento inteligente de rotas.",descricao:"Encontre os melhores caminhos para a sua rotina, sem complicação.",cor:"#3975ff"},
 {icone:"location-outline",titulo:"Localização em tempo real.",descricao:"Acompanhe sua posição e siga viagem com mais tranquilidade.",cor:"#3975ff"},
 {icone:"hardware-chip-outline",titulo:"Assistente de viagem automatizado.",descricao:"Receba orientações em cada etapa, da partida ao seu destino.",cor:"#8757ed"},
 {icone:"time-outline",titulo:"Horários do transporte público.",descricao:"Consulte as próximas partidas e organize melhor o seu tempo.",cor:"#3975ff"},
 {icone:"wallet-outline",titulo:"Planejamento econômico.",descricao:"Compare opções de transporte e faça seu orçamento render mais.",cor:"#3975ff"},
 {icone:"sparkles-outline",titulo:"Assistente de inteligência artificial.",descricao:"Tire dúvidas e descubra novas formas de se mover pela cidade.",cor:"#8757ed"}
] as const;
const gradiente=(value:string):ViewStyle=>Platform.OS==="web"?({backgroundImage:value} as ViewStyle):{};

export default function TelaInicial({abrir}:{abrir:()=>void}){
 const {width,height}=useWindowDimensions();
 const mobile=width<760;
 const scroll=useRef<ScrollView>(null);
 const sobre=useRef(0), funcionalidades=useRef(0);
 const ir=(y:number)=>scroll.current?.scrollTo({y,animated:true});
 const heroHeight=mobile?Math.max(600,height):Math.max(660,Math.min(1000,Math.round(width*.59)));
 return <ScrollView ref={scroll} style={s.page} contentContainerStyle={{flexGrow:1}}>
   <View style={[s.hero,{minHeight:heroHeight}]}>
     <Image source={heroImage} style={s.image} resizeMode="cover" accessible={false}/>
     <View pointerEvents="none" style={[s.overlay,Platform.OS==="web"&&gradiente(mobile?"linear-gradient(90deg, rgba(5,12,25,.93), rgba(5,12,25,.53))":"linear-gradient(90deg, #070f1e 0%, rgba(7,15,30,.97) 20%, rgba(7,15,30,.75) 43%, rgba(7,15,30,.25) 76%, rgba(7,15,30,.19) 100%)")]}/>
     <View style={[s.wrap,s.heroWrap,mobile&&s.mobileWrap]}>
       <View style={[s.header,mobile&&s.headerMobile]}>
         <Text style={s.brand}>citizen <Text style={s.brandAccent}>tech</Text></Text>
         <View style={s.nav}>
           <Pressable accessibilityRole="button" onPress={()=>ir(sobre.current)} style={s.navItem}><Text style={s.navText}>O projeto</Text></Pressable>
           <Pressable accessibilityRole="button" onPress={()=>ir(funcionalidades.current)} style={s.navItem}><Text style={s.navText}>Funcionalidades</Text></Pressable>
         </View>
         {!mobile&&<Text style={s.city}>SÃO PAULO, SP</Text>}
       </View>
       <View style={[s.heroBody,mobile&&s.heroBodyMobile]}>
         <Text style={[s.eyebrow,s.heroEyebrow]}>MOBILIDADE URBANA · SÃO PAULO</Text>
         <Text accessibilityRole="header" style={[s.heading,mobile&&s.headingMobile]}>O futuro da{"\n"}mobilidade é{"\n"}<Text style={s.cyan}>para todos.</Text></Text>
         <Text style={s.description}>Tecnologia que conecta pessoas, transforma caminhos{"\n"}e aproxima você da cidade.</Text>
         <Pressable accessibilityRole="button" onPress={abrir} style={({pressed})=>[s.primary,pressed&&{opacity:.8}]}><Text style={s.primaryText}>Acessar projeto</Text><Ionicons name="arrow-forward" size={19} color="#fff"/></Pressable>
       </View>
       <View style={s.heroFoot}><Text style={s.micro}>INTELIGÊNCIA QUE MOVE A CIDADE.</Text><Pressable accessibilityRole="button" onPress={()=>ir(sobre.current)} style={s.explore}><Text style={s.exploreText}>Explore o projeto</Text><Ionicons name="arrow-down" size={13} color="#b7c6db"/></Pressable></View>
     </View>
   </View>
   <View onLayout={e=>sobre.current=e.nativeEvent.layout.y} style={s.about}>
     <View style={[s.wrap,s.aboutWrap,mobile&&s.mobileWrap,mobile&&s.stack]}>
       <View style={s.aboutLeft}><Text style={s.eyebrow}>TECNOLOGIA COM PROPÓSITO</Text><Text accessibilityRole="header" style={[s.sectionTitle,mobile&&s.sectionTitleMobile]}>Uma cidade.{"\n"}Infinitas possibilidades.</Text></View>
       <View style={s.aboutRight}><Text style={s.aboutText}>O Citizen Tech usa inteligência artificial para simplificar seus deslocamentos em São Paulo. Mais autonomia para escolher, acessibilidade para chegar e economia para ir além — no ritmo da sua vida.</Text>
         <View style={s.metrics}>{[{nome:"Autonomia",cor:"#3e75ff"},{nome:"Acessibilidade",cor:"#9260f1"},{nome:"Economia",cor:"#55cfe7"}].map(m=><View key={m.nome} style={s.metric}><View style={[s.metricLine,{backgroundColor:m.cor}]}/><Text style={s.metricText}>{m.nome}</Text></View>)}</View>
       </View>
     </View>
   </View>
   <View onLayout={e=>funcionalidades.current=e.nativeEvent.layout.y} style={s.resources}>
     <View style={[s.wrap,s.resourceWrap,mobile&&s.mobileWrap]}>
       <Text style={s.eyebrow}>INTELIGÊNCIA EM CADA TRAJETO</Text><Text accessibilityRole="header" style={[s.sectionTitle,mobile&&s.sectionTitleMobile]}>Seu caminho, mais inteligente.</Text><Text style={s.resourceSub}>Tudo o que você precisa para se mover melhor.</Text>
       <View style={[s.grid,mobile&&s.stack]}>{recursos.map(r=><View key={r.titulo} style={[s.card,mobile&&s.cardMobile]}><Ionicons name={r.icone} size={24} color={r.cor}/><Text style={s.cardTitle}>{r.titulo}</Text><Text style={s.cardText}>{r.descricao}</Text></View>)}</View>
     </View>
   </View>
   <View style={[s.closing,gradiente("linear-gradient(110deg,#080f20 0%,#101f43 59%,#15346d 100%)")]}><Text style={s.closingEyebrow}>A CIDADE EVOLUI. VOCÊ VAI JUNTO.</Text><Text accessibilityRole="header" style={[s.closingTitle,mobile&&s.closingMobile]}>Transformando a mobilidade.{"\n"}<Text style={s.cyan}>Conectando o futuro.</Text></Text></View>
   <View style={s.footer}><View style={[s.wrap,s.footerWrap,mobile&&s.mobileWrap]}><Text style={s.footerBrand}>citizen tech</Text><View style={s.footerRight}><Text style={s.footerText}>FIAP</Text><Text style={s.footerText}>Global Solution 2026</Text></View></View></View>
 </ScrollView>;
}
const s=StyleSheet.create({
 page:{flex:1,backgroundColor:"#fff"},wrap:{width:"100%",maxWidth:1440,alignSelf:"center",paddingHorizontal:64},
 mobileWrap:{paddingHorizontal:24},hero:{position:"relative",overflow:"hidden",backgroundColor:"#070f1e",borderBottomWidth:4,borderBottomColor:"#149de5"},
 image:{...StyleSheet.absoluteFillObject,width:"100%",height:"100%"},overlay:{...StyleSheet.absoluteFillObject,backgroundColor:Platform.OS==="web"?"transparent":"rgba(5,12,25,.69)"},
 heroWrap:{flex:1,justifyContent:"space-between"},header:{minHeight:104,flexDirection:"row",alignItems:"center",borderBottomWidth:1,borderBottomColor:"rgba(178,199,227,.16)",gap:32},
 headerMobile:{minHeight:80,flexWrap:"wrap",gap:12,paddingVertical:12},brand:{fontSize:27,letterSpacing:-1.2,fontWeight:"600",color:"#fff"},brandAccent:{color:"#64d7ef",fontWeight:"400"},
 nav:{marginLeft:"auto",flexDirection:"row",alignItems:"center",gap:32},navItem:{minHeight:44,justifyContent:"center"},navText:{color:"#d8e3f3",fontSize:13},city:{fontSize:11,letterSpacing:.6,color:"#8699b4"},
 heroBody:{paddingVertical:65,maxWidth:720,alignItems:"flex-start",gap:24,flex:1,justifyContent:"center"},heroBodyMobile:{paddingVertical:48,gap:20},
 eyebrow:{fontSize:11,letterSpacing:1.6,fontWeight:"700",color:"#3972fb"},heroEyebrow:{color:"#6bd4f1"},
 heading:{color:"#fff",fontSize:76,lineHeight:82,fontWeight:"600",letterSpacing:-3.4},headingMobile:{fontSize:47,lineHeight:53,letterSpacing:-1.9},cyan:{color:"#64d4eb"},
 description:{fontSize:17,lineHeight:27,color:"#b8c5d8",maxWidth:550},primary:{minHeight:54,minWidth:224,paddingHorizontal:23,flexDirection:"row",alignItems:"center",justifyContent:"space-between",gap:22,backgroundColor:"#2463ed",borderRadius:6},primaryText:{fontSize:14,fontWeight:"600",color:"#fff"},
 heroFoot:{paddingBottom:30,paddingTop:14,flexDirection:"row",justifyContent:"space-between",alignItems:"center",gap:10},micro:{fontSize:9,color:"#97acc9",letterSpacing:1.7},explore:{flexDirection:"row",alignItems:"center",gap:8,minHeight:44},exploreText:{color:"#b7c6db",fontSize:11},
 about:{backgroundColor:"#fff"},aboutWrap:{paddingVertical:82,flexDirection:"row",alignItems:"flex-start",gap:75},aboutLeft:{flex:1,gap:24},aboutRight:{flex:1,gap:40,paddingTop:38},
 sectionTitle:{fontSize:44,lineHeight:50,letterSpacing:-1.8,fontWeight:"600",color:"#101e36"},sectionTitleMobile:{fontSize:32,lineHeight:38,letterSpacing:-1.1},
 aboutText:{fontSize:17,lineHeight:28,color:"#63748c",maxWidth:560},metrics:{flexDirection:"row",gap:30,justifyContent:"space-between"},metric:{flex:1,gap:10},metricLine:{width:24,height:3,borderRadius:1},metricText:{fontSize:13,fontWeight:"500",color:"#20334d"},
 resources:{backgroundColor:"#f2f5fb"},resourceWrap:{paddingVertical:68,gap:19},resourceSub:{color:"#73839a",fontSize:15,lineHeight:23},grid:{flexDirection:"row",flexWrap:"wrap",justifyContent:"space-between",gap:20,marginTop:20},
 card:{width:"31.9%",backgroundColor:"#fff",borderWidth:1,borderColor:"#e3e9f1",borderRadius:10,padding:25,minHeight:176,gap:17},cardMobile:{width:"100%",minHeight:148},cardTitle:{fontSize:17,fontWeight:"600",color:"#14243c"},cardText:{fontSize:14,lineHeight:22,color:"#718199"},
 stack:{flexDirection:"column",gap:20},closing:{paddingVertical:74,paddingHorizontal:24,alignItems:"center",gap:24,backgroundColor:"#101f43"},closingEyebrow:{fontSize:10,letterSpacing:2,color:"#9cb1d0"},closingTitle:{fontSize:46,lineHeight:55,letterSpacing:-1.6,fontWeight:"600",color:"#fff",textAlign:"center"},closingMobile:{fontSize:31,lineHeight:38},
 footer:{backgroundColor:"#080f1d"},footerWrap:{paddingVertical:28,flexDirection:"row",alignItems:"center",justifyContent:"space-between",gap:12},footerBrand:{fontSize:19,fontWeight:"500",color:"#dbe6fa"},footerRight:{flexDirection:"row",gap:40,flexWrap:"wrap"},footerText:{fontSize:11,color:"#9badc8"}
});
