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

  updateRating(movieId: number, rating: number): Observable<Movie> {
    return this.http.put<Movie>(`${this.baseUrl}/${movieId}/rating`, { rating_perso: rating });
  }

  /** Sans `query` : titre/annee du nom de dossier ; avec `query` : recherche manuelle. */
  searchTmdb(movieId: number, query?: string, year?: number | null): Observable<TmdbCandidate[]> {
    let params = new HttpParams();
    if (query !== undefined) params = params.set('query', query);
    if (query !== undefined && year) params = params.set('year', year);
    return this.http.get<TmdbCandidate[]>(`${this.baseUrl}/${movieId}/tmdb-search`, { params });
  }

  updateMetadata(movieId: number, tmdbId: number): Observable<Movie> {
    return this.http.put<Movie>(`${this.baseUrl}/${movieId}/metadata`, { tmdb_id: tmdbId });
  }

  /** Sans `videoId` : fichier principal du film ; avec `videoId` : un episode precis d'une serie. */
  playMovie(movieId: number, videoId?: number): Observable<{ status: string; file: string }> {
    let params = new HttpParams();
    if (videoId !== undefined) params = params.set('video_id', videoId);
    return this.http.post<{ status: string; file: string }>(`${this.baseUrl}/${movieId}/play`, {}, { params });
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
