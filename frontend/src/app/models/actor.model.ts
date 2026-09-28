export interface ActorSearchResult {
  name: string;
  movie_count: number;
}

export interface ActorFilmographyEntry {
  tmdb_movie_id: number;
  title: string;
  year: number | null;
  poster_filename: string | null;
  in_library: boolean;
  movie_id: number | null;
  folder_name: string | null;
}

export interface ActorFilmography {
  name: string;
  // 'tmdb' : filmographie complete recuperee depuis TheMovieDB.
  // 'local' : TMDb interroge mais indisponible / acteur non trouve (repli).
  // 'local_only' : TMDb non interroge (mode "bibliotheque uniquement").
  source: 'tmdb' | 'local' | 'local_only';
  movies_in_library: number;
  total_movies: number;
  movies: ActorFilmographyEntry[];
}
