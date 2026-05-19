// services/feed.ts

export type OportunidadeItem = {
  id: string;
  titulo?: string;
  resumo?: string;
  tipo?: string;
  fonte?: string;
  pais?: string;
  score?: number;
  link?: string;
  prazo?: string | null;
};

const BASE_URL = "http://192.168.0.14:8000"; // seu IP

export async function fetchFeed(): Promise<OportunidadeItem[]> {
  const response = await fetch(`${BASE_URL}/feed_app`);

  if (!response.ok) {
    throw new Error("Erro ao carregar feed");
  }

  const data = await response.json();

  return data.items || [];
}