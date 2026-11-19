import React from "react";
import {router} from "expo-router";
import TelaInicial from "../components/TelaInicial";

export default function Inicio(){
 return <TelaInicial abrir={()=>router.push("/projeto")}/>;
}
