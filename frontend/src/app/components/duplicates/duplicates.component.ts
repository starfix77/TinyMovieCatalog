import { Component, computed, effect, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Movie, VideoFile } from '../../models/movie.model';
import { LibraryService } from '../../services/library.service';
import { MovieService } from '../../services/movie.service';

interface DuplicateGroup {
  key: string;
  title: string;
  year: number | null;
  movies: Movie[];
  files: { movie: Movie; file: VideoFile }[];
  posterUrl: string | null;
}

@Component({
  selector: 'app-duplicates',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './duplicates.component.html',
  styleUrl: './duplicates.component.css',
})
export class DuplicatesComponent {
  readonly libraryService = inject(LibraryService);
  private readonly movieService = inject(MovieService);
  readonly groups = signal<DuplicateGroup[]>([]);
  readonly loading = signal(false);
  readonly error = signal('');
  readonly collapsed = signal<Set<string>>(new Set());
  private requestToken = 0;

  constructor() {
    effect(() => {
      const libraryId = this.libraryService.activeLibraryId();
      this.libraryService.moviesRefreshTick();
      if (libraryId) this.load(libraryId);
      else this.groups.set([]);
    });
  }

  private load(libraryId: number): void {
    const token = ++this.requestToken;
    this.loading.set(true);
    this.error.set('');
    this.movieService.listMovies(libraryId).subscribe({
      next: (page) => {
        if (token !== this.requestToken) return;
        const map = new Map<string, { movies: Movie[]; files: { movie: Movie; file: VideoFile }[] }>();
        for (const movie of page.items) {
          const files = movie.video_files ?? [];
          if (!files.length) continue;
          const key = this.normalize(movie.title);
          const group = map.get(key) ?? { movies: [], files: [] };
          group.movies.push(movie);
          for (const file of files) group.files.push({ movie, file });
          map.set(key, group);
        }
        const groups: DuplicateGroup[] = [];
        for (const [key, group] of map) {
          if (group.files.length < 2) continue;
          const representative = group.movies[0];

          if (!representative) {
            continue;
          }
          
          groups.push({
            key,
            title: representative.title,
            year: representative.year,
            movies: group.movies,
            files: group.files,
            posterUrl: this.movieService.posterUrl(representative),
          });
        }
        this.groups.set(groups.sort((a, b) => a.title.localeCompare(b.title, 'fr')));
        this.loading.set(false);
      },
      error: () => {
        if (token !== this.requestToken) return;
        this.error.set('Impossible de charger les fichiers de la bibliothèque.');
        this.loading.set(false);
      },
    });
  }

  private normalize(value: string): string {
    return (value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('fr').trim();
  }

  toggle(key: string): void {
    this.collapsed.update((current) => {
      const next = new Set(current);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  isCollapsed(key: string): boolean { return this.collapsed().has(key); }

  formatSize(bytes: number): string {
    if (!bytes) return '—';
    if (bytes >= 1024 ** 3) return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
    if (bytes >= 1024 ** 2) return `${(bytes / 1024 ** 2).toFixed(0)} MB`;
    return `${(bytes / 1024).toFixed(0)} KB`;
  }

  formatBitrate(bitsPerSec: number | null): string {
    return bitsPerSec ? `${Math.round(bitsPerSec / 1000)} kb/s` : '—';
  }

  trackGroup(_: number, group: DuplicateGroup): string { return group.key; }
  trackFile(_: number, item: { movie: Movie; file: VideoFile }): number { return item.file.id; }
}
