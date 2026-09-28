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

  formatDate(value: string | null): string | null {
    if (!value) return null;
    const date = new Date(value);
    return isNaN(date.getTime()) ? null : this.dateFormatter.format(date);
  }
}
