import React from "react";
import { View } from "react-native";

export default function MapaPreview({ url }: { url: string }) {
  return <View style={{ height: 330, borderRadius: 18, overflow: "hidden", width: "100%" }}>
    {React.createElement("iframe", {
      src: url,
      title: "Mapa interativo da viagem",
      loading: "lazy",
      referrerPolicy: "no-referrer-when-downgrade",
      style: { width: "100%", height: "100%", border: 0 },
      allowFullScreen: true,
    })}
  </View>;
}
