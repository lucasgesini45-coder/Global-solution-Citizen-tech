import { useEffect } from "react";
import { Platform } from "react-native";
import { Stack } from "expo-router";

export default function Layout() {
  useEffect(() => {
    if (Platform.OS !== "web" || typeof document === "undefined") return;
    const id = "citizen-font-sora";
    if (document.getElementById(id)) return;
    const link = document.createElement("link");
    link.id = id;
    link.rel = "stylesheet";
    link.href = "https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700;800&display=swap";
    document.head.appendChild(link);
  }, []);
  return <Stack screenOptions={{ headerShown: false }} />;
}
