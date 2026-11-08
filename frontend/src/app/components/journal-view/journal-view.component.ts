import { Component, computed, effect, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';

import { LibraryService } from '../../services/library.service';
import { JournalService } from '../../services/journal.service';
import {
  JournalEntry, JournalFile, JournalFileAudio, JournalFileStatus,
} from '../../models/journal.model';

/** Un film / une serie du detail d'un evenement : vignette + fichiers concernes. */
interface JournalMovieGroup {
  key: string;
  title: string;
  year: number | null;
  poster: string | null;
  files: JournalFile[];
}

/** Vue « Journal » : historique des evenements de la bibliotheque active. */
@Component({
  selector: 'app-journal-view',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './journal-view.component.html',
  styleUrl: './journal-view.component.css',
})
export class JournalViewComponent {
  private readonly libraryService = inject(LibraryService);
  private readonly journalService = inject(JournalService);

  readonly isTv = computed(() => this.libraryService.activeLibrary()?.media_type === 'tv');
  readonly entries = signal<JournalEntry[]>([]);
  readonly loading = signal(false);
  readonly error = signal('');

  /** Evenements dont le detail est affiche, et detail deja charge (par id). */
  readonly expanded = signal<Set<number>>(new Set());
  readonly groups = signal<Record<number, JournalMovieGroup[]>>({});
  readonly loadingDetail = signal<Set<number>>(new Set());
  readonly detailError = signal<Record<number, string>>({});
  private requestToken = 0;

  constructor() {
    effect(() => {
      const libraryId = this.libraryService.activeLibraryId();
      this.libraryService.moviesRefreshTick(); // fin de scan / modification de bibliotheque
      this.load(libraryId);
    }, { allowSignalWrites: true });
  }

  private load(libraryId: number | null): void {
    const token = ++this.requestToken;
    this.expanded.set(new Set());
    this.groups.set({});
    if (!libraryId) {
      this.entries.set([]);
      this.loading.set(false);
      return;
    }
    this.loading.set(true);
    this.error.set('');
    this.journalService.list(libraryId).subscribe({
      next: (res) => {
        if (token !== this.requestToken) return;
        this.entries.set(res.items);
        this.loading.set(false);
      },
      error: () => {
        if (token !== this.requestToken) return;
        this.error.set('Impossible de charger le journal.');
        this.loading.set(false);
      },
    });
  }

  // ---------- Libelles ----------

  actionLabel(entry: JournalEntry): string {
    switch (entry.action) {
      case 'create': return 'Création';
      case 'update': return 'Modification de la bibliothèque';
      default: return 'Scan';
    }
  }

  /** Options de scan, ex. « Comparaison simple · Structure simple ». */
  scanOptions(entry: JournalEntry): string {
    if (entry.action !== 'scan' || !entry.compare_mode) return '';
    const parts = [entry.compare_mode === 'deep' ? 'Comparaison approfondie' : 'Comparaison simple'];
    if (this.isTv()) {
      parts.push(`Profondeur ${entry.max_depth ?? ''}`.trim());
    } else {
      parts.push(entry.structure_mode === 'simple' ? 'Structure simple' : 'Structure mixte');
    }
    return parts.join(' · ');
  }

  statusLabel(status: JournalFileStatus): string {
    return status === 'created' ? 'Créé' : status === 'modified' ? 'Modifié' : 'Supprimé';
  }

  hasDetails(entry: JournalEntry): boolean {
    return entry.files_added + entry.files_modified + entry.files_deleted > 0;
  }

  formatSize(bytes: number | null): string {
    if (!bytes) return '—';
    const gb = bytes / 1024 / 1024 / 1024;
    return gb >= 1 ? `${gb.toFixed(2)}GB` : `${(bytes / 1024 / 1024).toFixed(0)}MB`;
  }

  resolution(file: JournalFile): string {
    return file.width && file.height ? `${file.width}x${file.height}` : '—';
  }

  formatBitrate(bitsPerSec: number | null): string {
    return bitsPerSec ? `${(bitsPerSec / 1000).toFixed(0)} kb/s` : '—';
  }

  trackLabel(track: JournalFileAudio): string {
    return `${track.language || 'und'} · ${track.codec || '?'} · ${this.formatBitrate(track.bitrate)}`;
  }

  poster(group: JournalMovieGroup): string | null {
    return this.journalService.posterUrl(group.poster);
  }

  // ---------- Masquer / afficher les details ----------

  isExpanded(id: number): boolean {
    return this.expanded().has(id);
  }

  toggle(entry: JournalEntry): void {
    if (!this.hasDetails(entry)) return;
    const next = new Set(this.expanded());
    if (next.has(entry.id)) {
      next.delete(entry.id);
      this.expanded.set(next);
      return;
    }
    next.add(entry.id);
    this.expanded.set(next);
    if (!this.groups()[entry.id]) this.loadDetail(entry.id);
  }

  private loadDetail(logId: number): void {
    this.loadingDetail.update((s) => new Set(s).add(logId));
    this.detailError.update((e) => ({ ...e, [logId]: '' }));
    this.journalService.files(logId).subscribe({
      next: (files) => {
        this.groups.update((g) => ({ ...g, [logId]: this.groupByMovie(files) }));
        this.stopLoading(logId);
      },
      error: () => {
        this.detailError.update((e) => ({ ...e, [logId]: 'Impossible de charger le détail.' }));
        this.stopLoading(logId);
      },
    });
  }

  private stopLoading(logId: number): void {
    this.loadingDetail.update((s) => {
      const next = new Set(s);
      next.delete(logId);
      return next;
    });
  }

  /** Regroupe les fichiers par film / serie (une serie = plusieurs episodes). */
  private groupByMovie(files: JournalFile[]): JournalMovieGroup[] {
    const map = new Map<string, JournalMovieGroup>();
    for (const file of files) {
      const key = file.movie_id !== null ? `m${file.movie_id}` : `f${file.id}`;
      let group = map.get(key);
      if (!group) {
        group = {
          key,
          title: file.movie_title || file.filename,
          year: file.movie_year,
          poster: file.poster_filename,
          files: [],
        };
        map.set(key, group);
      }
      group.files.push(file);
    }
    return [...map.values()];
  }
}
