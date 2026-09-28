import { Component, OnInit, inject, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { LibraryService } from '../../services/library.service';
import { Library } from '../../models/library.model';

@Component({
  selector: 'app-library-selector',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './library-selector.component.html',
  styleUrl: './library-selector.component.css',
})
export class LibrarySelectorComponent implements OnInit {
  private readonly libraryService = inject(LibraryService);

  readonly libraries = this.libraryService.libraries;
  readonly activeLibraryId = this.libraryService.activeLibraryId;

  showAddForm = signal(false);
  newName = '';
  newPath = '';
  formError = signal<string | null>(null);

  scanningId = signal<number | null>(null);
  scanMessage = signal<string | null>(null);
  readonly scanProgress = this.libraryService.scanProgress;
  private scanSockets = new Map<number, WebSocket>();
  pendingDeleteId = signal<number | null>(null);

  constructor() {
    effect(() => {
      const progress = this.scanProgress();
      if (!progress) return;
      if (progress.status === 'completed' || progress.status === 'failed') {
        this.scanningId.set(null);
        const lib = this.libraries().find((item) => item.id === progress.library_id);
        if (lib) {
          this.scanMessage.set(
            progress.status === 'completed'
              ? `"${lib.name}" : scan termine${progress.result?.errors?.length ? ` avec ${progress.result.errors.length} avertissement(s).` : '.'}`
              : `Echec du scan de "${lib.name}" : ${progress.error ?? 'erreur inconnue'}.`
          );
          setTimeout(() => this.scanMessage.set(null), 6000);
        }
        this.scanSockets.get(progress.library_id)?.close();
        this.scanSockets.delete(progress.library_id);
      }
    });
  }

  ngOnInit(): void {
    this.refresh();
  }

  refresh(): void {
    this.libraryService.loadLibraries().subscribe();
  }

  select(lib: Library): void {
    this.libraryService.setActiveLibrary(lib.id);
  }

  openAddForm(): void {
    this.newName = '';
    this.newPath = '';
    this.formError.set(null);
    this.showAddForm.set(true);
  }

  cancelAddForm(): void {
    this.showAddForm.set(false);
  }

  submitAddForm(): void {
    const name = this.newName.trim();
    const rootPath = this.newPath.trim();
    if (!name || !rootPath) {
      this.formError.set('Le nom et le chemin du dossier sont obligatoires.');
      return;
    }
    this.libraryService.createLibrary({ name, root_path: rootPath }).subscribe({
      next: (lib) => {
        this.showAddForm.set(false);
        this.refresh();
        this.libraryService.setActiveLibrary(lib.id);
      },
      error: (err) => {
        this.formError.set(
          err?.error?.detail ?? "Impossible de creer la bibliotheque. Verifiez le chemin indique."
        );
      },
    });
  }

  askDelete(lib: Library, event: Event): void {
    event.stopPropagation();
    this.pendingDeleteId.set(lib.id);
  }

  cancelDelete(): void {
    this.pendingDeleteId.set(null);
  }

  confirmDelete(lib: Library): void {
    this.libraryService.deleteLibrary(lib.id).subscribe(() => {
      this.pendingDeleteId.set(null);
      this.refresh();
    });
  }

  scan(lib: Library, event: Event): void {
    event.stopPropagation();
    if (this.scanningId() === lib.id) return;

    this.scanningId.set(lib.id);
    this.scanMessage.set(null);

    this.libraryService.scanLibrary(lib.id).subscribe({
      next: () => {
        const socket = this.libraryService.watchScan(lib.id);
        this.scanSockets.get(lib.id)?.close();
        this.scanSockets.set(lib.id, socket);
      },
      error: () => {
        this.scanningId.set(null);
        this.scanMessage.set(`Echec du lancement du scan de "${lib.name}".`);
      },
    });
  }
}
