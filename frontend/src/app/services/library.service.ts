import { Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

import { environment } from '../../environments/environment';
import { Library, LibraryCreate, LibraryInfo, ScanResult, ScanProgress } from '../models/library.model';

@Injectable({ providedIn: 'root' })
export class LibraryService {
  private readonly baseUrl = `${environment.apiUrl}/libraries`;

  /** Liste des bibliotheques chargees, partagee par toute l'application. */
  readonly libraries = signal<Library[]>([]);
  /** Bibliotheque actuellement selectionnee sur la page principale. */
  readonly activeLibraryId = signal<number | null>(null);
  /** Incremente a chaque fin de scan : les pages "vignettes"/"tableau"
   *  s'y abonnent pour recharger la liste des films sans changer de
   *  bibliotheque. */
  readonly moviesRefreshTick = signal(0);
  readonly scanProgress = signal<ScanProgress | null>(null);
  readonly activeLibrary = computed(() => {
    const id = this.activeLibraryId();
    return this.libraries().find((lib) => lib.id === id) ?? null;
  });

  constructor(private http: HttpClient) {}

  loadLibraries(): Observable<Library[]> {
    return this.http.get<Library[]>(this.baseUrl).pipe(
      tap((libs) => {
        this.libraries.set(libs);
        // Si aucune bibliotheque active (ou celle-ci a ete supprimee), on
        // selectionne automatiquement la premiere disponible.
        const current = this.activeLibraryId();
        if (!current || !libs.some((l) => l.id === current)) {
          this.activeLibraryId.set(libs[0]?.id ?? null);
        }
      })
    );
  }

  getLibraryInfo(id: number): Observable<LibraryInfo> {
    return this.http.get<LibraryInfo>(`${this.baseUrl}/${id}/info`);
  }

  createLibrary(payload: LibraryCreate): Observable<Library> {
    return this.http.post<Library>(this.baseUrl, payload);
  }

  deleteLibrary(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}`);
  }

  scanLibrary(id: number): Observable<ScanProgress> {
    return this.http.post<ScanProgress>(`${this.baseUrl}/${id}/scan`, {});
  }

  watchScan(id: number): WebSocket {
    const wsUrl = this.baseUrl.replace(/^http/, 'ws') + `/${id}/scan/ws`;
    const socket = new WebSocket(wsUrl);
    socket.onmessage = (event) => {
      const progress = JSON.parse(event.data) as ScanProgress;
      this.scanProgress.set(progress);
      if (progress.status === 'completed') {
        this.loadLibraries().subscribe();
        this.notifyMoviesChanged();
      }
    };
    socket.onerror = () => {
      // Le scan continue cote serveur meme si le client perd la connexion.
    };
    socket.onclose = () => {
      const current = this.scanProgress();
      if (current?.library_id === id && current.status === 'running') {
        this.scanProgress.set({ ...current, status: 'running' });
      }
    };
    return socket;
  }

  setActiveLibrary(id: number): void {
    this.activeLibraryId.set(id);
  }

  /** A appeler apres un scan reussi pour forcer les vues "vignettes"/"tableau"
   *  a recharger la liste des films, meme si la bibliotheque active n'a pas
   *  change. */
  notifyMoviesChanged(): void {
    this.moviesRefreshTick.update((v) => v + 1);
  }
}