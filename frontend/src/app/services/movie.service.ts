import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { Movie, MoviePage, MoviePoster, SortDir, SortField, TmdbCandidate, TmdbLanguages } from '../models/movie.model';

@Injectable({ providedIn: 'root' })
export class MovieService {
  private readonly baseUrl = `${environment.apiUrl}/movies`;

  constructor(private http: HttpClient) {}

  listMovies(
    libraryId: number,
    search?: string,
    sortBy?: SortField,
    sortDir: SortDir = 'asc'
  ): Observable<MoviePage> {
    let params = new HttpParams().set('library_id', libraryId);
    if (search) params = params.set('search', search);
    if (sortBy) params = params.set('sort_by', sortBy).set('sort_dir', sortDir);
    return this.http.get<MoviePage>(this.baseUrl, { params });
  }

  getMovie(id: number): Observable<Movie> {
    return this.http.get<Movie>(`${this.baseUrl}/${id}`);
  }

  searchTmdb(movieId: number): Observable<TmdbCandidate[]> {
    return this.http.get<TmdbCandidate[]>(`${this.baseUrl}/${movieId}/tmdb-search`);
  }

  updateMetadata(movieId: number, tmdbId: number): Observable<Movie> {
    return this.http.put<Movie>(`${this.baseUrl}/${movieId}/metadata`, { tmdb_id: tmdbId });
  }

  playMovie(movieId: number): Observable<{ status: string; file: string }> {
    return this.http.post<{ status: string; file: string }>(`${this.baseUrl}/${movieId}/play`, {});
  }

  getTmdbLanguages(): Observable<TmdbLanguages> {
    return this.http.get<TmdbLanguages>(`${environment.apiUrl}/tmdb/languages`);
  }

  searchPosters(movieId: number, language: string): Observable<MoviePoster[]> {
    const params = new HttpParams().set('language', language);
    return this.http.get<MoviePoster[]>(`${this.baseUrl}/${movieId}/posters`, { params });
  }

  changePoster(movieId: number, filePath: string): Observable<Movie> {
    return this.http.put<Movie>(`${this.baseUrl}/${movieId}/poster`, { file_path: filePath });
  }

  tmdbThumbUrl(posterPath: string): string {
    return `https://image.tmdb.org/t/p/w342${posterPath}`;
  }

  tmdbPosterUrl(posterPath: string | null): string | null {
    return posterPath ? `https://image.tmdb.org/t/p/w500${posterPath}` : null;
  }

  posterUrl(movie: Movie): string | null {
    if (!movie.poster_filename) return null;
    // Cache-buster: force le navigateur a recharger l'affiche apres un remplacement.
    const version = encodeURIComponent(movie.poster_filename);
    return `${environment.apiUrl}/movies/${movie.id}/poster?v=${version}`;
  }
}
