import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { ActorFilmography, ActorSearchResult } from '../models/actor.model';

@Injectable({ providedIn: 'root' })
export class ActorService {
  private readonly baseUrl = `${environment.apiUrl}/actors`;

  constructor(private http: HttpClient) {}

  searchActors(libraryId: number, q: string): Observable<ActorSearchResult[]> {
    const params = new HttpParams().set('library_id', libraryId).set('q', q);
    return this.http.get<ActorSearchResult[]>(`${this.baseUrl}/search`, { params });
  }

  getFilmography(libraryId: number, name: string): Observable<ActorFilmography> {
    const params = new HttpParams().set('library_id', libraryId).set('name', name);
    return this.http.get<ActorFilmography>(`${this.baseUrl}/filmography`, { params });
  }

  /** Meme convention de nommage que les autres vignettes TMDb (tmdb_<id>.jpg),
   *  servie directement depuis le dossier statique partage. */
  posterUrl(posterFilename: string | null): string | null {
    if (!posterFilename) return null;
    return `${environment.staticUrl}/data/thumbnails/${encodeURIComponent(posterFilename)}`;
  }
}
