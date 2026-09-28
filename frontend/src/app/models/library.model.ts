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
  /** Taille du filesystem du dossier racine, deja formatee ("1.82 TB", "931.51 GB"). */
  fs_total_size: string | null;
  fs_free_size: string | null;
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
}
