import { Component, ElementRef, OnInit, ViewChild, inject, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, RouterLinkActive } from '@angular/router';

import { LibraryService } from '../../services/library.service';
import { Library, MediaType, ScanCompareMode } from '../../models/library.model';
import { MediaTypeIconComponent } from '../media-type-icon/media-type-icon.component';

@Component({
  selector: 'app-library-selector',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, RouterLinkActive, MediaTypeIconComponent],
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
  newMediaType: MediaType = 'movie';
  formError = signal<string | null>(null);

  scanningId = signal<number | null>(null);
  scanMessage = signal<string | null>(null);
  readonly scanProgress = this.libraryService.scanProgress;
  private scanSockets = new Map<number, WebSocket>();
  pendingDeleteId = signal<number | null>(null);

  // ---------- Boite de dialogue de confirmation de scan ----------
  scanDialogLibrary = signal<Library | null>(null);
  scanCompareMode: ScanCompareMode = 'simple';
  scanStructureMode: 'simple' | 'mixed' = 'mixed';
  scanMaxDepth = 1;

  @ViewChild('scanYesBtn') private scanYesBtnRef?: ElementRef<HTMLButtonElement>;

  constructor() {
    effect(() => {
      // Place le focus par defaut sur le bouton "Oui" a l'ouverture de la boite.
      if (this.scanDialogLibrary()) {
        setTimeout(() => this.scanYesBtnRef?.nativeElement.focus());
      }
    });

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

  /** Libelle du compteur : "12 films" ou "3 series". */
  countLabel(lib: Library): string {
    const n = lib.movie_count;
    return lib.media_type === 'tv' ? `${n} série${n > 1 ? 's' : ''}` : `${n} film${n > 1 ? 's' : ''}`;
  }

  select(lib: Library): void {
    this.libraryService.setActiveLibrary(lib.id);
  }

  openAddForm(): void {
    this.newName = '';
    this.newPath = '';
    this.newMediaType = 'movie';
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
    this.libraryService.createLibrary({ name, root_path: rootPath, media_type: this.newMediaType }).subscribe({
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

  /** Ouvre la boite de dialogue de confirmation avant de lancer un scan. */
  askScan(lib: Library, event: Event): void {
    event.stopPropagation();
    if (this.scanningId() === lib.id) return;

    this.scanCompareMode = 'simple';
    this.scanStructureMode = 'mixed';
    // Series : dossier de la serie puis dossiers de saisons = 2 niveaux.
    this.scanMaxDepth = lib.media_type === 'tv' ? 2 : 1;
    this.scanDialogLibrary.set(lib);
  }

  cancelScanDialog(): void {
    this.scanDialogLibrary.set(null);
  }

  confirmScanDialog(): void {
    const lib = this.scanDialogLibrary();
    if (!lib) return;
    const compareMode = this.scanCompareMode;
    const structureMode = this.scanStructureMode;
    const maxDepth = Math.max(0, Math.min(20, Number(this.scanMaxDepth) || 0));
    this.scanDialogLibrary.set(null);
    this.scan(lib, compareMode, structureMode, maxDepth);
  }

  private scan(lib: Library, compareMode: ScanCompareMode, structureMode: 'simple' | 'mixed', maxDepth: number): void {
    if (this.scanningId() === lib.id) return;

    this.scanningId.set(lib.id);
    this.scanMessage.set(null);

    this.libraryService.scanLibrary(lib.id, compareMode, structureMode, maxDepth).subscribe({
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
