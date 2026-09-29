export interface Library {
  id: number;
  name: string;
  root_path: string;
  created_at: string;
  last_scanned_at: string | null;
  movie_count: number;
}

/** Fiche d'information d'une bibliotheque (page "Info"). */
export interface LibraryInfo {
  id: number;
  name: string;
  root_path: string;
  movie_count: number;
  created_at: string | null;
  last_scanned_at: string | null;
  /** Taille totale et espace libre du filesystem du dossier racine, en octets. */
  fs_total_size: number | null;
  fs_free_size: number | null;
  /** false si le dossier racine est inaccessible (valeurs = derniere lecture connue). */
  fs_available: boolean;
}

export interface LibraryCreate {
  name: string;
  root_path: string;
}

export interface ScanResult {
  library_id: number;
  folders_scanned: number;
  movies_added: number;
  movies_updated: number;
  movies_removed: number;
  errors: string[];
}

export interface ScanProgress {
  library_id: number;
  status: 'idle' | 'queued' | 'running' | 'completed' | 'failed';
  current: number;
  total: number;
  progress: number;
  current_folder: string | null;
  result?: ScanResult | null;
  error?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  compare_mode?: 'simple' | 'deep';
}

/** Mode de comparaison utilise lors d'un scan de bibliotheque.
 *  - simple : identification des films par nom de dossier uniquement (mode historique).
 *  - deep   : compare en plus le nom du fichier video principal avec celui deja
 *             enregistre en base, et ne relance ffprobe que s'il a change. */
export type ScanCompareMode = 'simple' | 'deep';

/** Mode de comparaison entre deux bibliotheques (vue "Comparaison"). */
export type CompareMode = 'identical' | 'missing_right' | 'missing_left';
/** Profondeur : simple = nom du dossier ; deep = + nom et taille du fichier video. */
export type CompareDepth = 'simple' | 'deep';
export type CompareStatus = 'identical' | 'identical_different_file' | 'missing_right' | 'missing_left';

export interface CompareAudioTrack {
  language: string | null;
  codec: string | null;
  bitrate: number | null;
  title: string | null;
}

/** Detail du fichier video principal (meme contenu que le bloc "Fichier video" de la fiche film). */
export interface CompareVideoDetail {
  filename: string;
  video_codec: string | null;
  width: number | null;
  height: number | null;
  size_bytes: number;
  duration_sec: number | null;
  audio_tracks: CompareAudioTrack[];
  subtitles: string[];
}

export interface CompareRow {
  left: string | null;
  right: string | null;
  left_movie_id?: number | null;
  right_movie_id?: number | null;
  status: CompareStatus;
  left_detail?: CompareVideoDetail | null;
  right_detail?: CompareVideoDetail | null;
}

export interface CompareResult {
  left_library_id: number;
  left_library_name: string;
  right_library_id: number;
  right_library_name: string;
  mode: CompareMode;
  depth: CompareDepth;
  total: number;
  rows: CompareRow[];
}
