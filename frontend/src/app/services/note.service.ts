import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { Note, NoteList } from '../models/note.model';

@Injectable({ providedIn: 'root' })
export class NoteService {
  constructor(private http: HttpClient) {}

  /** Note d'un film / d'une serie (contenu vide si aucune note). */
  getNote(movieId: number): Observable<Note> {
    return this.http.get<Note>(`${environment.apiUrl}/movies/${movieId}/note`);
  }

  /** Enregistre la note (un texte vide supprime la note). */
  saveNote(movieId: number, content: string): Observable<Note> {
    return this.http.put<Note>(`${environment.apiUrl}/movies/${movieId}/note`, { content });
  }

  /** Tous les films / series de la bibliotheque ayant une note. */
  listNotes(libraryId: number): Observable<NoteList> {
    const params = new HttpParams().set('library_id', libraryId);
    return this.http.get<NoteList>(`${environment.apiUrl}/notes`, { params });
  }
}
