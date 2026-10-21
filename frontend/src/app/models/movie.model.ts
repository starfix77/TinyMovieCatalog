export interface AudioTrack {
  id: number;
  track_index: number;
  language: string | null;
  title: string | null;
  codec: string | null;
  channels: number | null;
  bitrate: number | null;
}

export interface VideoFile {
  id: number;
  filename: string;
  filepath: string;
  container: string | null;
  size_bytes: number;
  duration_sec: number | null;
  video_codec: string | null;
  width: number | null;
  height: number | null;
  video_bitrate: number | null;
  audio_tracks: AudioTrack[];
}

export interface Subtitle {
  id: number;
  filename: string;
  language_guess: string | null;
}

export interface CastMember {
  name: string;
  character: string;
}

export interface Movie {
  id: number;
  library_id: number;
  folder_name: string;
  title: string;
  year: number | null;
  tmdb_id: number | null;
  original_title: string | null;
  overview: string | null;
  release_date: string | null;
  poster_filename: string | null;
  cast: string | null; // JSON string, voir CastMember[]
  genres: string | null;
  vote_average: number | null; // note moyenne TMDB (0-10)
  media_type?: 'movie' | 'tv'; // type de la bibliotheque (une serie TV est une entree "movie" cote base)
  rating_perso: number; // note personnelle (0-5, pas de 0.5)
  video_files: VideoFile[];
  subtitles: Subtitle[];
}

export interface TmdbCandidate {
  tmdb_id: number;
  title: string;
  original_title: string;
  overview: string;
  release_date: string;
  poster_path: string | null;
  genres: string;
  cast: string;
}

export interface TmdbLanguage {
  code: string; // ex: fr-FR
  english_name: string;
  native_name: string;
}

export interface TmdbLanguages {
  default: string;
  languages: TmdbLanguage[];
}

export interface MoviePoster {
  file_path: string;
  width: number;
  height: number;
  language: string | null;
  vote_average: number;
}

export interface MoviePage {
  total: number;
  items: Movie[];
}

export type SortField = 'title' | 'filename' | 'video_codec' | 'resolution' | 'size' | 'genre' | 'year' | 'duration' | 'vote_average' | 'rating';
export type SortDir = 'asc' | 'desc';
