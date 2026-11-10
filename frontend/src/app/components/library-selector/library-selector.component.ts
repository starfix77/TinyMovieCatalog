import { Component, ElementRef, OnInit, ViewChild, inject, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, RouterLinkActive } from '@angular/router';

import { LibraryService } from '../../services/library.service';
import { Library, MediaType, ScanCompareMode } from '../../models/library.model';
import { MediaTypeIconComponent } from '../media-type-icon/media-type-icon.component';

/** Version affichee dans la fenetre "A propos" (a garder alignee avec le <h1> du template). */
export const APP_VERSION = '0.9.31';

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

  // ---------- Reorganisation des bibliotheques (glisser-deposer) ----------
  /** Bibliotheque en cours de deplacement. */
  draggedId = signal<number | null>(null);
  /** Cible courante du survol : l'indicateur s'affiche avant ou apres cette bibliotheque. */
  dropTarget = signal<{ id: number; position: 'before' | 'after' } | null>(null);
  reorderError = signal<string | null>(null);

  // ---------- Boite de dialogue de confirmation de scan ----------
  scanDialogLibrary = signal<Library | null>(null);
  scanCompareMode: ScanCompareMode = 'simple';
  scanStructureMode: 'simple' | 'mixed' = 'mixed';
  scanMaxDepth = 1;

  // ---------- Boite de dialogue de modification d'une bibliotheque ----------
  editDialogLibrary = signal<Library | null>(null);
  editName = '';
  editPath = '';
  editMediaType: MediaType = 'movie';
  editError = signal<string | null>(null);
  editSaving = signal(false);

  // ---------- Boite de dialogue "A propos" ----------
  aboutOpen = signal(false);
  readonly appVersion = APP_VERSION;

  @ViewChild('scanYesBtn') private scanYesBtnRef?: ElementRef<HTMLButtonElement>;
  @ViewChild('aboutOkBtn') private aboutOkBtnRef?: ElementRef<HTMLButtonElement>;

  constructor() {
    effect(() => {
      // Place le focus par defaut sur le bouton "Oui" a l'ouverture de la boite.
      if (this.scanDialogLibrary()) {
        setTimeout(() => this.scanYesBtnRef?.nativeElement.focus());
      }
    });

    effect(() => {
      // Place le focus sur le bouton "OK" a l'ouverture de la fenetre "A propos".
      if (this.aboutOpen()) {
        setTimeout(() => this.aboutOkBtnRef?.nativeElement.focus());
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

  // ---------- Glisser-deposer : ordre d'affichage des bibliotheques ----------

  onDragStart(lib: Library, event: DragEvent): void {
    this.draggedId.set(lib.id);
    this.reorderError.set(null);
    if (event.dataTransfer) {
      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.setData('text/plain', String(lib.id)); // requis par Firefox
    }
  }

  onDragOver(lib: Library, event: DragEvent): void {
    const dragged = this.draggedId();
    if (dragged === null) return; // glissement externe (fichier, texte...) : ignore
    event.preventDefault();
    if (event.dataTransfer) event.dataTransfer.dropEffect = 'move';

    if (dragged === lib.id) {
      this.dropTarget.set(null);
      return;
    }
    // Moitie haute de l'element = avant, moitie basse = apres.
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
    const position = event.clientY < rect.top + rect.height / 2 ? 'before' : 'after';
    const current = this.dropTarget();
    if (current?.id !== lib.id || current.position !== position) {
      this.dropTarget.set({ id: lib.id, position });
    }
  }

  onDrop(lib: Library, event: DragEvent): void {
    event.preventDefault();
    const dragged = this.draggedId();
    const target = this.dropTarget();
    this.endDrag();
    if (dragged === null || !target || target.id !== lib.id) return;

    const current = this.libraries().map((item) => item.id);
    const reordered = current.filter((id) => id !== dragged);
    const index = reordered.indexOf(target.id);
    if (index < 0) return;
    reordered.splice(target.position === 'after' ? index + 1 : index, 0, dragged);
    if (reordered.every((id, i) => id === current[i])) return; // ordre inchange

    this.libraryService.reorderLibraries(reordered).subscribe({
      error: () => {
        this.reorderError.set("Impossible d'enregistrer le nouvel ordre des bibliotheques.");
        setTimeout(() => this.reorderError.set(null), 6000);
      },
    });
  }

  /** Fin du glissement (depot ou annulation, ex. touche Echap) : retire les indicateurs. */
  endDrag(): void {
    this.draggedId.set(null);
    this.dropTarget.set(null);
  }

  /** Quitte la liste sans deposer : retire l'indicateur de depot. */
  onListDragLeave(event: DragEvent): void {
    const list = event.currentTarget as HTMLElement;
    if (!event.relatedTarget || !list.contains(event.relatedTarget as Node)) {
      this.dropTarget.set(null);
    }
  }

  /** Ouvre la fenetre "A propos" (double-clic sur le titre <h1>). */
  openAbout(): void {
    this.aboutOpen.set(true);
  }

  closeAbout(): void {
    this.aboutOpen.set(false);
  }

  /** Ouvre la boite de dialogue de modification d'une bibliotheque. */
  askEdit(lib: Library, event: Event): void {
    event.stopPropagation();
    this.editName = lib.name;
    this.editPath = lib.root_path;
    this.editMediaType = lib.media_type ?? 'movie';
    this.editError.set(null);
    this.editSaving.set(false);
    this.editDialogLibrary.set(lib);
  }

  cancelEditDialog(): void {
    this.editDialogLibrary.set(null);
  }

  confirmEditDialog(): void {
    const lib = this.editDialogLibrary();
    if (!lib || this.editSaving()) return;

    const name = this.editName.trim();
    const rootPath = this.editPath.trim();
    if (!name || !rootPath) {
      this.editError.set('Le nom et le dossier racine sont obligatoires.');
      return;
    }

    this.editSaving.set(true);
    this.editError.set(null);
    this.libraryService.updateLibrary(lib.id, { name, root_path: rootPath, media_type: this.editMediaType }).subscribe({
      next: () => {
        this.editSaving.set(false);
        this.editDialogLibrary.set(null);
      },
      error: (err) => {
        this.editSaving.set(false);
        this.editError.set(err?.error?.detail ?? 'Impossible de modifier la bibliotheque.');
      },
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
