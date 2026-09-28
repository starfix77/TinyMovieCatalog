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
  source: 'tmdb' | 'local';
  movies_in_library: number;
  total_movies: number;
  movies: ActorFilmographyEntry[];
}
