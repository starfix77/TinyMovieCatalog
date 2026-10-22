import { Component, ElementRef, OnDestroy, ViewChild, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { LibraryService } from '../../services/library.service';
import { LibraryExportSummary, LibraryImportResult, ThumbnailJob } from '../../models/library.model';

type Phase = 'idle' | 'conflict' | 'importing' | 'thumbnails' | 'done';

const EXPORT_FORMAT = 'TinyMovieCatalog.library';

/**
 * Vue « Importer une bibliothèque » : le bouton « Importer » ouvre la sélection
 * d'un fichier d'export (.tmcatalog.json), l'importe dans la base SQLite, force
 * le téléchargement des vignettes absentes de data/thumbnails (tâche de fond
 * côté serveur, avec barre de progression) puis réactualise le bandeau de gauche.
 */
@Component({
  selector: 'app-library-import',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './library-import.component.html',
  styleUrls: ['../library-tools/tools-shared.css', './library-import.component.css'],
})
export class LibraryImportComponent implements OnDestroy {
  private readonly libraryService = inject(LibraryService);
  private readonly router = inject(Router);

  @ViewChild('fileInput') private fileInput?: ElementRef<HTMLInputElement>;

  readonly phase = signal<Phase>('idle');
  readonly fileName = signal<string | null>(null);
  readonly summary = signal<LibraryExportSummary | null>(null);
  readonly error = signal<string | null>(null);
  readonly conflictMessage = signal<string | null>(null);
  readonly result = signal<LibraryImportResult | null>(null);
  readonly job = signal<ThumbnailJob | null>(null);

  /** Valeurs modifiables (utilisées quand le dossier racine existe déjà). */
  editName = '';
  editPath = '';

  private data: unknown = null;
  private pollTimer: ReturnType<typeof setTimeout> | null = null;

  openPicker(): void {
    this.fileInput?.nativeElement.click();
  }

  async onFileSelected(event: Event): Promise<void> {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = ''; // permet de re-sélectionner le même fichier
    if (!file) return;

    this.reset();
    this.fileName.set(file.name);

    let parsed: any;
    try {
      parsed = JSON.parse(await file.text());
    } catch {
      this.error.set("Fichier illisible : ce n'est pas un export JSON valide.");
      return;
    }

    const lib = parsed?.library;
    if (parsed?.format !== EXPORT_FORMAT || !lib?.name || !lib?.root_path || !Array.isArray(parsed?.movies)) {
      this.error.set("Ce fichier n'est pas un export de bibliothèque TinyMovieCatalog.");
      return;
    }

    this.data = parsed;
    this.summary.set({
      name: lib.name,
      root_path: lib.root_path,
      media_type: lib.media_type === 'tv' ? 'tv' : 'movie',
      movie_count: parsed.movies.length,
    });
    this.editName = lib.name;
    this.editPath = lib.root_path;

    if (this.pathTaken(this.editPath)) {
      this.conflictMessage.set('Une bibliothèque utilise déjà ce dossier racine. Modifiez-le pour importer une copie.');
      this.phase.set('conflict');
    } else {
      this.runImport();
    }
  }

  confirmConflict(): void {
    if (!this.editName.trim() || !this.editPath.trim()) return;
    if (this.pathTaken(this.editPath)) {
      this.conflictMessage.set('Ce dossier racine est déjà utilisé par une bibliothèque existante.');
      return;
    }
    this.runImport();
  }

  cancel(): void {
    this.reset();
  }

  openLibrary(): void {
    const res = this.result();
    if (!res) return;
    this.libraryService.setActiveLibrary(res.library.id);
    this.router.navigateByUrl('/');
  }

  progressPercent(): number {
    const job = this.job();
    return job && job.total > 0 ? Math.round((job.done / job.total) * 100) : 0;
  }

  ngOnDestroy(): void {
    this.stopPolling();
  }

  // ---------- Import ----------

  private runImport(): void {
    const summary = this.summary();
    if (!summary) return;

    this.phase.set('importing');
    this.error.set(null);
    this.conflictMessage.set(null);

    const name = this.editName.trim() !== summary.name ? this.editName.trim() : undefined;
    const path = this.editPath.trim() !== summary.root_path ? this.editPath.trim() : undefined;

    this.libraryService.importLibrary(this.data, name, path).subscribe({
      next: (res) => {
        this.result.set(res);
        // La bibliothèque existe déjà en base : on l'affiche tout de suite dans le bandeau.
        this.libraryService.loadLibraries().subscribe();
        if (res.thumbnail_job_id) {
          this.phase.set('thumbnails');
          this.poll(res.thumbnail_job_id);
        } else {
          this.finish();
        }
      },
      error: (err) => {
        if (err?.status === 409) {
          this.conflictMessage.set(err?.error?.detail ?? 'Ce dossier racine est déjà utilisé.');
          this.phase.set('conflict');
        } else {
          this.error.set(err?.error?.detail ?? "L'import a échoué. Vérifiez que le serveur est démarré.");
          this.phase.set('idle');
        }
      },
    });
  }

  private poll(jobId: string): void {
    this.libraryService.getThumbnailJob(jobId).subscribe({
      next: (job) => {
        this.job.set(job);
        if (job.status === 'completed') {
          this.finish();
        } else {
          this.pollTimer = setTimeout(() => this.poll(jobId), 1000);
        }
      },
      error: () => {
        // Suivi impossible (serveur redémarré ?) : la bibliothèque est tout de même importée.
        this.finish();
      },
    });
  }

  /** Fin du traitement : réactualise le bandeau de gauche et les vues films. */
  private finish(): void {
    this.stopPolling();
    this.libraryService.loadLibraries().subscribe();
    this.libraryService.notifyMoviesChanged();
    this.phase.set('done');
  }

  private pathTaken(path: string): boolean {
    const wanted = path.trim();
    return this.libraryService.libraries().some((lib) => lib.root_path === wanted);
  }

  private stopPolling(): void {
    if (this.pollTimer) {
      clearTimeout(this.pollTimer);
      this.pollTimer = null;
    }
  }

  private reset(): void {
    this.stopPolling();
    this.phase.set('idle');
    this.fileName.set(null);
    this.summary.set(null);
    this.error.set(null);
    this.conflictMessage.set(null);
    this.result.set(null);
    this.job.set(null);
    this.data = null;
  }
}
