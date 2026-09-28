export interface SagaListItem {
  id: number;
  name: string;
  poster_filename: string | null;
  movies_in_library: number;
  total_movies: number;
}

export interface SagaMovieEntry {
  tmdb_movie_id: number;
  title: string;
  year: number | null;
  poster_filename: string | null;
  in_library: boolean;
  movie_id: number | null;
  folder_name: string | null;
}

export interface SagaDetail {
  id: number;
  name: string;
  overview: string | null;
  poster_filename: string | null;
  movies: SagaMovieEntry[];
}
