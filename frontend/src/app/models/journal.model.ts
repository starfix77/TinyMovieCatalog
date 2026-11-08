/** Evenement du journal au niveau bibliotheque. */
export type JournalAction = 'create' | 'update' | 'scan';

export interface JournalEntry {
  id: number;
  action: JournalAction;
  details: string | null;
  compare_mode: 'simple' | 'deep' | null;
  structure_mode: 'simple' | 'mixed' | null;
  max_depth: number | null;
  files_added: number;
  files_modified: number;
  files_deleted: number;
  created_at: string;
}

export interface JournalList {
  total: number;
  items: JournalEntry[];
}

export type JournalFileStatus = 'created' | 'modified' | 'deleted';

export interface JournalFileAudio {
  language: string | null;
  codec: string | null;
  bitrate: number | null;
  channels: number | null;
}

/** Detail d'un fichier film / episode concerne par un evenement de scan. */
export interface JournalFile {
  id: number;
  status: JournalFileStatus;
  movie_id: number | null;
  movie_title: string | null;
  movie_year: number | null;
  poster_filename: string | null;
  filename: string;
  size_bytes: number | null;
  video_codec: string | null;
  width: number | null;
  height: number | null;
  audio_tracks: JournalFileAudio[];
  subtitles: string[];
  created_at: string;
}
