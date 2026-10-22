import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { LibraryService } from '../../services/library.service';
import { Library } from '../../models/library.model';
import { MediaTypeIconComponent } from '../media-type-icon/media-type-icon.component';

/**
 * Vue « Exporter une bibliothèque » : liste des bibliothèques, choix d'une
 * seule, puis sauvegarde de toutes ses informations dans un fichier JSON
 * (.tmcatalog.json) réimportable via la vue « Importer une bibliothèque ».
 */
@Component({
  selector: 'app-library-export',
  standalone: true,
  imports: [CommonModule, RouterLink, MediaTypeIconComponent],
  templateUrl: './library-export.component.html',
  styleUrls: ['../library-tools/tools-shared.css', './library-export.component.css'],
})
export class LibraryExportComponent {
  private readonly libraryService = inject(LibraryService);

  readonly libraries = this.libraryService.libraries;
  readonly selectedId = signal<number | null>(this.libraryService.activeLibraryId());
  readonly exporting = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal<string | null>(null);

  select(library: Library): void {
    this.selectedId.set(library.id);
    this.error.set(null);
    this.success.set(null);
  }

  countLabel(lib: Library): string {
    const unit = lib.media_type === 'tv' ? 'série' : 'film';
    return `${lib.movie_count} ${unit}${lib.movie_count > 1 ? 's' : ''}`;
  }

  export(): void {
    const library = this.libraries().find((l) => l.id === this.selectedId());
    if (!library || this.exporting()) return;

    this.exporting.set(true);
    this.error.set(null);
    this.success.set(null);

    this.libraryService.exportLibrary(library.id).subscribe({
      next: async (blob) => {
        try {
          const saved = await this.saveBlob(blob, this.fileName(library));
          if (saved) this.success.set(`« ${library.name} » exportée (${this.countLabel(library)}).`);
        } catch {
          this.error.set("L'enregistrement du fichier a échoué.");
        } finally {
          this.exporting.set(false);
        }
      },
      error: () => {
        this.error.set("L'export a échoué. Vérifiez que le serveur est démarré.");
        this.exporting.set(false);
      },
    });
  }

  private fileName(library: Library): string {
    const slug = library.name.replace(/[^A-Za-z0-9_-]+/g, '_').replace(/^_+|_+$/g, '') || 'bibliotheque';
    return `${slug}.tmcatalog.json`;
  }

  /** Boîte « Enregistrer sous » si le navigateur la propose, sinon téléchargement classique.
   *  Retourne false si l'utilisateur annule. */
  private async saveBlob(blob: Blob, fileName: string): Promise<boolean> {
    const picker = (window as any).showSaveFilePicker as
      | ((options: unknown) => Promise<any>)
      | undefined;
    if (picker) {
      try {
        const handle = await picker({
          suggestedName: fileName,
          types: [{ description: 'Export de bibliothèque TinyMovieCatalog',
                    accept: { 'application/json': ['.json'] } }],
        });
        const writable = await handle.createWritable();
        await writable.write(blob);
        await writable.close();
        return true;
      } catch (err: any) {
        if (err?.name === 'AbortError') return false;
        throw err;
      }
    }

    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = fileName;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 10_000);
    return true;
  }
}
