import { Stack } from "expo-router";

// A interface usa a fonte nativa do sistema: SF Pro no iOS e equivalente
// disponível em cada plataforma. Sem download de fonte externa.
export default function Layout() {
  return <Stack screenOptions={{ headerShown: false }} />;
}
