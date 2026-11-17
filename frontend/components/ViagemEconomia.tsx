import React,{useState} from "react";
import {Pressable,StyleSheet,Text,TextInput,View,Linking} from "react-native";
import {Ionicons} from "@expo/vector-icons";
import type {HorarioOnibus} from "./HorariosOnibus";

export type EtapaViagem={inicio_geo?:{lat:number;lon:number}|null;fim_geo?:{lat:number;lon:number}|null;etapa:number;modal:string;linha?:string|null;cor_linha?:string|null;operadora?:string|null;sentido?:string|null;de?:string|null;para?:string|null;partida?:string|null;chegada?:string|null;tempo_real?:boolean;tempo_min?:number|null;paradas?:string[]};
export type CustoViagem={centavos:number|null;integracao_centavos?:number|null;integracao_condicao?:string|null;status:string;detalhes:{linha:string;centavos:number}[];pendencias:string[];fontes:string[];data_referencia:string;aviso:string};
export type AlternativaEconomica={id:number;tempo_min:number;caminhada_m:number|null;etapas_viagem:EtapaViagem[];horarios_onibus:HorarioOnibus[];custo:CustoViagem;trajeto:number[][];trechos:any[];modal:string};
const dinheiro=(n:number)=>"R$ "+(n/100).toFixed(2).replace(".",",");
function hora(t?:string|null){if(!t)return "Não informado";const d=new Date(t);return Number.isNaN(d.getTime())?"Não informado":new Intl.DateTimeFormat("pt-BR",{timeZone:"America/Sao_Paulo",day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit",hourCycle:"h23"}).format(d);}
const modo=(e:EtapaViagem)=>e.modal==="WALK"?"A pé":e.modal==="BUS"?"Ônibus":e.modal==="SUBWAY"||e.modal==="METRO"?"Metrô":e.modal==="TRAM"?"VLT":"Transporte ferroviário";

function Voltar({onPress}:{onPress:()=>void}){return <Pressable style={s.back} onPress={onPress} accessibilityRole="button"><Ionicons name="arrow-back-outline" size={18} color="#0069d2"/><Text style={s.link}>Voltar ao planejamento</Text></Pressable>}
function Botao({titulo,onPress,secondary=false,disabled=false}:{titulo:string;onPress:()=>void;secondary?:boolean;disabled?:boolean}){return <Pressable accessibilityRole="button" disabled={disabled} onPress={onPress} style={[s.button,secondary&&s.secondary,disabled&&{opacity:.45}]}><Text style={[s.buttonText,secondary&&{color:"#0069d2"}]}>{titulo}</Text></Pressable>}
export function AssistenteViagem({etapas,indice,setIndice,voltar,horarios,recalcular,temRota,carregando,gpsAtivo,statusGPS,mapa}:{etapas:EtapaViagem[];indice:number;setIndice:(n:number)=>void;voltar:()=>void;horarios:()=>void;recalcular:()=>void;temRota:boolean;carregando:boolean;gpsAtivo:boolean;statusGPS:string;mapa:React.ReactNode}){
 const atual=etapas[indice], seguinte=etapas[indice+1], total=etapas.length;
 const encerrada=total>0&&indice>=total;
 return <View style={s.page}>
   <Text style={s.eyebrow}>ACOMPANHAMENTO DE VIAGEM</Text><Text style={s.heading}>Assistente de viagem</Text><Text style={s.sub}>Ative o GPS para acompanhar o percurso e avançar automaticamente nas etapas reconhecidas. O modo manual continua disponível.</Text><Voltar onPress={voltar}/>
   {mapa}
   <Text style={s.sub}>{statusGPS} · {gpsAtivo?"Avanço automático quando o GPS confirma o percurso.":"Ative o GPS para habilitar avanço automático."}</Text>
   {!temRota||!total?<View style={s.card}><Text style={s.title}>Calcule um trajeto para começar</Text><Text style={s.sub}>Assim que o itinerário estiver disponível, suas instruções aparecerão aqui.</Text></View>:<>
     <View style={s.card}>
       <View style={s.row}><Text style={s.title}>Progresso da viagem</Text><Text style={s.link}>{Math.min(indice,total)} de {total} etapas concluídas</Text></View>
       <View style={s.track}><View style={[s.fill,{width:(Math.min(indice,total)/total*100).toFixed(2)+"%" as `${number}%`}]}/></View>
       {encerrada?<><Text style={s.heading}>Viagem concluída</Text><Text style={s.sub}>Todas as etapas foram concluídas no acompanhamento.</Text><Botao titulo="Reiniciar acompanhamento" onPress={()=>setIndice(0)} secondary/></>:atual&&<>
         <Text style={s.eyebrow}>ETAPA ATUAL · {indice+1}</Text><Text style={s.heading}>{modo(atual)}{atual.linha?" · "+atual.linha:""}</Text>
         <View style={s.stop}><Text style={s.label}>{atual.modal==="WALK"?"PONTO DE PARTIDA":"EMBARQUE"}</Text><Text style={s.title}>{atual.de||"Não informado"}</Text><Text style={s.label}>{atual.modal==="WALK"?"DESTINO DA CAMINHADA":"DESEMBARQUE"}</Text><Text style={s.title}>{atual.para||"Não informado"}</Text>{!!atual.sentido&&<Text style={s.sub}>Sentido: {atual.sentido}</Text>}</View>
         <Text style={s.sub}>Partida: {hora(atual.partida)}  ·  Chegada: {hora(atual.chegada)}{atual.tempo_min!=null?"  ·  "+atual.tempo_min+" min":""}</Text>
         <Text style={s.sub}>{atual.tempo_real?"Horários informados com dados em tempo real na consulta original; não são atualizados automaticamente.":"Horários do itinerário, sem confirmação em tempo real."}</Text>
         {!!atual.paradas?.length&&<Text style={s.sub}>Paradas intermediárias: {atual.paradas.join(" · ")}</Text>}
         {seguinte&&<Text style={s.sub}>Próxima etapa: {modo(seguinte)} {seguinte.linha||""} — {seguinte.de||"ponto não informado"}</Text>}
         {gpsAtivo&&(!atual.inicio_geo||!atual.fim_geo)&&<Text style={s.sub}>Coordenadas desta etapa indisponíveis; confirme manualmente.</Text>}
         <Botao titulo={indice===total-1?"Concluir viagem":"Concluir etapa e avançar"} onPress={()=>setIndice(indice+1)}/>
         <Botao titulo="Etapa anterior" onPress={()=>setIndice(Math.max(0,indice-1))} secondary disabled={indice===0}/>
       </>}
       <Botao titulo="Consultar horários de ônibus" onPress={horarios} secondary/>
       <Botao titulo={carregando?"Recalculando...":"Recalcular a partir do planejador"} onPress={recalcular} disabled={carregando} secondary/>
       <Text style={s.sub}>Em caso de atraso, perda de conexão ou mudança de percurso, confirme sua localização no planejador e calcule uma nova rota. O GPS funciona somente com o aplicativo aberto e autorização. Em túneis, estações próximas ou leitura imprecisa, confirme manualmente. Não garante acessibilidade.</Text>
     </View>
     <View style={s.card}><Text style={s.title}>Todas as etapas</Text>{etapas.map((e,i)=><Pressable key={i} onPress={()=>setIndice(i)} style={s.item} accessibilityRole="button"><Ionicons name={i<indice?"checkmark-circle":i===indice?"radio-button-on-outline":"ellipse-outline"} size={20} color={i<indice?"#008e5a":"#0069d2"}/><View style={{flex:1}}><Text style={s.title}>{modo(e)} {e.linha||""}</Text><Text style={s.sub}>{e.de||"Origem"} → {e.para||"Destino"}</Text></View></Pressable>)}</View>
   </>}
 </View>;
}
export function PlanejamentoEconomico({opcoes,selecionada,selecionar,voltar,temRota}:{opcoes:AlternativaEconomica[];selecionada:number|null;selecionar:(o:AlternativaEconomica)=>void;voltar:()=>void;temRota:boolean}){
 const [orcamento,setOrcamento]=useState("10,00");
 const [bilheteUnico,setBilheteUnico]=useState(false);
 const custoOpcao=(o:AlternativaEconomica)=>bilheteUnico?(o.custo.integracao_centavos??o.custo.centavos):o.custo.centavos;
 const valido=/^\d{1,5}([,.]\d{1,2})?$/.test(orcamento.trim());
 const limite=valido?Math.round(Number(orcamento.replace(",","."))*100):null;
 const classificadas=[...opcoes].sort((a,b)=>(custoOpcao(a)??Infinity)-(custoOpcao(b)??Infinity)||a.tempo_min-b.tempo_min);
 return <View style={s.page}>
 <Text style={s.eyebrow}>MOBILIDADE QUE CABE NO BOLSO</Text><Text style={s.heading}>Planejamento econômico</Text><Text style={s.sub}>Compare itinerários disponíveis para o mesmo trajeto e modal. Valores de referência, não garantia de cobrança.</Text><Voltar onPress={voltar}/>
 <View style={s.card}><Text style={s.title}>Quanto você pode gastar?</Text><Text style={s.sub}>Orçamento de uma viagem (ida), em reais.</Text><TextInput accessibilityLabel="Orçamento em reais" keyboardType="decimal-pad" value={orcamento} onChangeText={setOrcamento} style={s.input} maxLength={8}/>{!valido&&<Text style={s.error}>Informe um valor válido, como 10,50.</Text>}<Pressable onPress={()=>setBilheteUnico(x=>!x)} style={s.item} accessibilityRole="checkbox" accessibilityState={{checked:bilheteUnico}}><Ionicons name={bilheteUnico?"checkbox":"square-outline"} color="#0069d2" size={22}/><View style={{flex:1}}><Text style={s.title}>Considerar Bilhete Único Comum</Text><Text style={s.sub}>Estimativa de integração quando houver dados suficientes e as condições de embarque forem atendidas. Não verifica seu saldo ou elegibilidade.</Text></View></Pressable></View>
 {!temRota||!opcoes.length?<View style={s.card}><Text style={s.title}>Nenhuma opção disponível</Text><Text style={s.sub}>Calcule um trajeto no planejador para consultar as alternativas. Caminhadas podem não ter custo de passagem.</Text></View>:classificadas.map(o=>{
 const custo=custoOpcao(o);const dentro=limite!==null&&custo!==null&&custo<=limite;
 return <View key={o.id} style={s.card}><View style={s.row}><Text style={s.title}>Opção {o.id}{selecionada===o.id?" · Selecionada":""}</Text><Text style={s.heading}>{custo===null?"Indefinido":dinheiro(custo)}</Text></View>
 <Text style={s.sub}>{o.tempo_min} min · {o.caminhada_m==null?"Caminhada não informada":(o.caminhada_m/1000).toFixed(2)+" km a pé"}</Text>
 <Text style={[s.label,{color:custo===null||limite===null?"#64748b":dentro?"#008e5a":"#9d4f20"}]}>{custo===null?"CUSTO NÃO CONFIRMADO":limite===null?"INFORME O ORÇAMENTO":dentro?"ESTIMATIVA DENTRO DO ORÇAMENTO":"ESTIMATIVA ACIMA DO ORÇAMENTO"}</Text>
 <Text style={s.sub}>{o.etapas_viagem.map(e=>modo(e)+(e.linha?" "+e.linha:"")).join(" → ")}</Text>
 {bilheteUnico&&o.custo.integracao_centavos!=null&&<Text style={s.sub}>{o.custo.integracao_condicao} Total avulso de referência: {dinheiro(o.custo.centavos??0)}.</Text>}
 {bilheteUnico&&o.custo.integracao_centavos==null&&<Text style={s.sub}>Sem confirmação suficiente para estimar integração; exibe o cenário avulso quando conhecido.</Text>}
 <Text style={s.label}>REFERÊNCIAS AVULSAS POR EMBARQUE</Text>
 {o.custo.detalhes.map((d,i)=><View key={i} style={s.row}><Text style={s.sub}>{d.linha}</Text><Text style={s.title}>{dinheiro(d.centavos)}</Text></View>)}
 {o.custo.pendencias.map((p,i)=><Text key={i} style={s.error}>{p}</Text>)}
 <Botao titulo="Usar esta alternativa" onPress={()=>selecionar(o)} secondary={selecionada===o.id}/>
 </View>})}
 <View style={s.card}><Text style={s.title}>Como os custos são calculados</Text><Text style={s.sub}>Tarifa comum municipal SPTrans: R$ 5,30; ônibus municipais gratuitos aos domingos quando a data/operadora são identificadas; rede ferroviária convencional identificada: R$ 5,40 por embarque. A referência integrada ônibus + trilhos é R$ 9,38 com Bilhete Único Comum e condições específicas. Por padrão, o cálculo soma tarifas avulsas. A opção Bilhete Único aplica uma estimativa de integração somente quando a operação e os horários fornecem dados suficientes. Benefícios pessoais e gratuidades especiais não são presumidos. Linhas especiais, intermunicipais e operadoras não identificadas ficam sem estimativa completa.</Text>
 {["https://www.sptrans.com.br/tarifas","https://www.metro.sp.gov.br/sua-viagem/bilhetes-cartoes/","https://www.sptrans.com.br/perguntas-e-respostas/?sobre=tarifa-zero"].map(u=><Pressable key={u} onPress={()=>{void Linking.openURL(u).catch(()=>{})}} accessibilityRole="link"><Text style={s.link}>{u}</Text></Pressable>)}
 <Text style={s.sub}>Referências consultadas em 17/11/2026. Confirme valores e regras atuais antes de viajar. Não há garantia de economia nem de percurso acessível.</Text></View>
 </View>;
}
const s=StyleSheet.create({page:{paddingVertical:24,gap:14},eyebrow:{fontSize:11,color:"#0069d2",fontWeight:"600",letterSpacing:1.2},heading:{fontSize:26,color:"#1d2633",fontWeight:"600"},title:{fontSize:15,fontWeight:"600",color:"#1d2633"},sub:{fontSize:13,lineHeight:20,color:"#64748b"},label:{fontSize:11,fontWeight:"600",color:"#64748b"},link:{color:"#0069d2",fontWeight:"600",fontSize:12},card:{padding:18,gap:12,backgroundColor:"#fff",borderRadius:20,borderWidth:1,borderColor:"#d9e6f5"},row:{flexDirection:"row",alignItems:"center",justifyContent:"space-between",gap:8,flexWrap:"wrap"},back:{flexDirection:"row",gap:7,alignItems:"center",alignSelf:"flex-start",paddingVertical:8},track:{height:8,borderRadius:8,backgroundColor:"#e4edf5",overflow:"hidden"},fill:{height:8,backgroundColor:"#0071e3"},stop:{backgroundColor:"#f1f6fc",borderRadius:12,padding:14,gap:8},button:{minHeight:44,borderRadius:12,backgroundColor:"#0071e3",alignItems:"center",justifyContent:"center",padding:12},secondary:{backgroundColor:"#eaf3fc"},buttonText:{fontSize:13,fontWeight:"600",color:"#fff",textAlign:"center"},item:{flexDirection:"row",alignItems:"center",gap:10,borderBottomWidth:1,borderBottomColor:"#eaf0f6",paddingVertical:10},input:{minHeight:48,borderRadius:10,backgroundColor:"#eff5fa",padding:12,fontSize:20,color:"#1d2633"},error:{fontSize:12,color:"#9d4f20"}});
