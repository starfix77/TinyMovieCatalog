import { Component, effect, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';

import { LibraryService } from '../../services/library.service';
import { LibraryInfo } from '../../models/library.model';

@Component({
  selector: 'app-library-info',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './library-info.component.html',
  styleUrl: './library-info.component.css',
})
export class LibraryInfoComponent {
  private readonly libraryService = inject(LibraryService);

  readonly activeLibraryId = this.libraryService.activeLibraryId;

  info = signal<LibraryInfo | null>(null);
  loading = signal(false);
  error = signal(false);

  private readonly dateFormatter = new Intl.DateTimeFormat('fr-FR', {
    dateStyle: 'long',
    timeStyle: 'short',
  });

  constructor() {
    // Recharge la fiche au changement de bibliotheque et apres un scan
    // (nombre de films, date de mise a jour et espace libre ont pu changer).
    effect(() => {
      this.activeLibraryId();
      this.libraryService.moviesRefreshTick();
      this.fetchInfo();
    });
  }

  fetchInfo(): void {
    const libId = this.activeLibraryId();
    this.info.set(null);
    this.error.set(false);
    if (!libId) return;

    this.loading.set(true);
    this.libraryService.getLibraryInfo(libId).subscribe({
      next: (info) => {
        this.info.set(info);
        this.loading.set(false);
      },
      error: () => {
        this.error.set(true);
        this.loading.set(false);
      },
    });
  }

  /** Octets -> "512 B", "1.50 KB", "12.30 MB", "931.51 GB", "1.82 TB" (base 1024,
   *  comme l'explorateur Windows). */
  formatSize(bytes: number | null): string {
    if (bytes === null || bytes === undefined) return '—';
    const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
    let value = bytes;
    let unit = 0;
    while (value >= 1024 && unit < units.length - 1) {
      value /= 1024;
      unit++;
    }
    return unit === 0 ? `${value} B` : `${value.toFixed(2)} ${units[unit]}`;
  }

  /** Espace utilise = taille totale - espace disponible (en octets). */
  usedBytes(lib: LibraryInfo): number | null {
    if (lib.fs_total_size === null || lib.fs_free_size === null) return null;
    return Math.max(lib.fs_total_size - lib.fs_free_size, 0);
  }

  /** Pourcentage du filesystem utilise (0-100, 1 decimale), ou null si inconnu. */
  usedPercent(lib: LibraryInfo): number | null {
    const used = this.usedBytes(lib);
    if (used === null || !lib.fs_total_size || lib.fs_total_size <= 0) return null;
    return Math.min(Math.round((used / lib.fs_total_size) * 1000) / 10, 100);
  }

  formatDate(value: string | null): string | null {
    if (!value) return null;
    const date = new Date(value);
    return isNaN(date.getTime()) ? null : this.dateFormatter.format(date);
  }
}
