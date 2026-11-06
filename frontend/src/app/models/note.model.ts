/** Note libre associee a un film ou a une serie. */
export interface Note {
  movie_id: number;
  content: string; // '' si aucune note
}

/** Ligne de la vue « Notes » : un film / une serie ayant une note. */
export interface NoteListItem {
  movie_id: number;
  title: string;
  year: number | null;
  folder_name: string;
  media_type: 'movie' | 'tv';
  content: string;
}

export interface NoteList {
  total: number;
  items: NoteListItem[];
}
