import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { JournalFile, JournalList } from '../models/journal.model';

@Injectable({ providedIn: 'root' })
export class JournalService {
  private readonly baseUrl = `${environment.apiUrl}/journal`;

  constructor(private http: HttpClient) {}

  /** Journal de la bibliotheque (niveau bibliotheque), du plus recent au plus ancien. */
  list(libraryId: number): Observable<JournalList> {
    const params = new HttpParams().set('library_id', libraryId);
    return this.http.get<JournalList>(this.baseUrl, { params });
  }

  /** Detail d'un evenement : fichiers films / series ajoutes, modifies ou supprimes. */
  files(logId: number): Observable<JournalFile[]> {
    return this.http.get<JournalFile[]>(`${this.baseUrl}/${logId}/files`);
  }

  posterUrl(posterFilename: string | null): string | null {
    return posterFilename ? `${environment.staticUrl}/data/thumbnails/${encodeURIComponent(posterFilename)}` : null;
  }
}
