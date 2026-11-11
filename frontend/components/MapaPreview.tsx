import React from "react";
import { View } from "react-native";
import WebView from "react-native-webview";

export default function MapaPreview({ url }: { url: string }) {
  return <View style={{ height: 330, borderRadius: 18, overflow: "hidden" }}>
    <WebView source={{ uri: url }} style={{ flex: 1 }} />
  </View>;
}
