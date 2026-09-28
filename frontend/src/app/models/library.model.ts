export interface Library {
  id: number;
  name: string;
  root_path: string;
  created_at: string;
  last_scanned_at: string | null;
  movie_count: number;
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
