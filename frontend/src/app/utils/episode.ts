/** Numero de saison / d'episode deduit d'un nom de fichier video. */
export interface EpisodeNumber {
  season: number | null;
  episode: number | null;
}

const RE_SXXEXX = /s(\d{1,2})[\s._-]?e(\d{1,4})/i; // S01E02
const RE_NXNN = /(?:^|[^\d])(\d{1,2})x(\d{2,3})(?!\d)/i; // 1x02
const RE_EPONLY = /(?:^|[\s._-])e(?:p(?:isode)?)?[\s._-]?(\d{1,4})(?!\d)/i; // E02, Ep02, Episode 02

export function parseEpisodeNumber(filename: string): EpisodeNumber {
  let m = RE_SXXEXX.exec(filename) ?? RE_NXNN.exec(filename);
  if (m) return { season: Number(m[1]), episode: Number(m[2]) };
  m = RE_EPONLY.exec(filename);
  if (m) return { season: null, episode: Number(m[1]) };
  return { season: null, episode: null };
}
