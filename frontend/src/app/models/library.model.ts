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
