import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { SagaDetail, SagaListItem } from '../models/saga.model';

@Injectable({ providedIn: 'root' })
export class SagaService {
  private readonly baseUrl = `${environment.apiUrl}/sagas`;

  constructor(private http: HttpClient) {}

  listSagas(libraryId: number): Observable<SagaListItem[]> {
    const params = new HttpParams().set('library_id', libraryId);
    return this.http.get<SagaListItem[]>(this.baseUrl, { params });
  }

  getSaga(sagaId: number, libraryId: number): Observable<SagaDetail> {
    const params = new HttpParams().set('library_id', libraryId);
    return this.http.get<SagaDetail>(`${this.baseUrl}/${sagaId}`, { params });
  }

  sagaPosterUrl(saga: SagaListItem | SagaDetail): string | null {
    if (!saga.poster_filename) return null;
    return `${environment.apiUrl}/sagas/${saga.id}/poster`;
  }

  /** Affiche d'un film de la saga (present ou non dans une bibliotheque) :
   *  meme convention de nom que les affiches "principales" des films
   *  (tmdb_<id>.jpg), servie directement depuis le dossier statique
   *  partage entre toutes les bibliotheques. */
  movieEntryPosterUrl(posterFilename: string | null): string | null {
    if (!posterFilename) return null;
    return `${environment.staticUrl}/data/thumbnails/${encodeURIComponent(posterFilename)}`;
  }
}
