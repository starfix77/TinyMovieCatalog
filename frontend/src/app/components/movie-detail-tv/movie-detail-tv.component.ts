import { Component, computed, effect, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { debounceTime, distinctUntilChanged, Subject } from 'rxjs';

import { LibraryService } from '../../services/library.service';
import { MovieService } from '../../services/movie.service';
import { Movie, VideoFile } from '../../models/movie.model';
import { parseEpisodeNumber } from '../../utils/episode';
import { MovieDetailComponent } from '../movie-detail/movie-detail.component';

type EpisodeSortKey = 'episode' | 'filename' | 'video_codec' | 'resolution' | 'size';
type SortDir = 'asc' | 'desc';

interface EpisodeColumn {
  key: EpisodeSortKey;
  label: string;
}

interface EpisodeRow {
  file: VideoFile;
  season: number | null;
  episode: number | null;
  label: string;
}

/** Vue « Détail technique » d'une bibliothèque de séries TV :
 *  une section dépliable par série, avec le tableau de ses épisodes. */
@Component({
  selector: 'app-movie-detail-tv',
  standalone: true,
  imports: [CommonModule, FormsModule, MovieDetailComponent],
  templateUrl: './movie-detail-tv.component.html',
  styleUrl: './movie-detail-tv.component.css',
})
export class MovieDetailTvComponent {
  private readonly libraryService = inject(LibraryService);
  private readonly movieService = inject(MovieService);

  readonly activeLibraryId = this.libraryService.activeLibraryId;

  readonly columns: EpisodeColumn[] = [
    { key: 'episode', label: 'N°' },
    { key: 'filename', label: 'Fichier video' },
    { key: 'video_codec', label: 'Encodage' },
    { key: 'resolution', label: 'Resolution' },
    { key: 'size', label: 'Taille' },
  ];

  search = '';
  private searchChanged = new Subject<string>();

  series = signal<Movie[]>([]);
  loading = signal(false);
  selectedMovie = signal<Movie | null>(null);

  /** Tri applique au tableau de chaque serie (par defaut : ordre alphabetique du fichier). */
  sortBy = signal<EpisodeSortKey>('filename');
  sortDir = signal<SortDir>('asc');

  /** Series actuellement depliees (par id). Repliees par defaut. */
  private expanded = signal<ReadonlySet<number>>(new Set());

  /** Lignes triees de chaque serie, recalculees uniquement si les donnees ou le tri changent. */
  readonly rowsBySeries = computed(() => {
    const key = this.sortBy();
    const dir = this.sortDir() === 'asc' ? 1 : -1;
    const map = new Map<number, EpisodeRow[]>();
    for (const movie of this.series()) {
      map.set(movie.id, this.buildRows(movie, key, dir));
    }
    return map;
  });

  constructor() {
    this.searchChanged.pipe(debounceTime(250), distinctUntilChanged()).subscribe(() => this.fetch());

    // allowSignalWrites : fetch() ecrit dans des signaux pendant l'effect.
    effect(() => {
      this.activeLibraryId();
      this.libraryService.moviesRefreshTick();
      this.fetch();
    }, { allowSignalWrites: true });
  }

  onSearchInput(): void {
    this.searchChanged.next(this.search);
  }

  fetch(): void {
    const libId = this.activeLibraryId();
    if (!libId) {
      this.series.set([]);
      return;
    }
    this.loading.set(true);
    this.movieService.listMovies(libId, this.search || undefined, 'title', 'asc').subscribe({
      next: (page) => {
        this.series.set(page.items);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  // ---------- Sections depliables ----------
  isExpanded(movie: Movie): boolean {
    return this.expanded().has(movie.id);
  }

  toggle(movie: Movie): void {
    this.expanded.update((set) => {
      const next = new Set(set);
      if (!next.delete(movie.id)) next.add(movie.id);
      return next;
    });
  }

  expandAll(): void {
    this.expanded.set(new Set(this.series().map((s) => s.id)));
  }

  collapseAll(): void {
    this.expanded.set(new Set());
  }

  get allExpanded(): boolean {
    const list = this.series();
    return list.length > 0 && list.every((s) => this.expanded().has(s.id));
  }

  // ---------- Tri ----------
  toggleSort(key: EpisodeSortKey): void {
    if (this.sortBy() === key) {
      this.sortDir.set(this.sortDir() === 'asc' ? 'desc' : 'asc');
    } else {
      this.sortBy.set(key);
      this.sortDir.set('asc');
    }
  }

  sortIcon(key: EpisodeSortKey): string {
    if (this.sortBy() !== key) return '';
    return this.sortDir() === 'asc' ? '▲' : '▼';
  }

  private buildRows(movie: Movie, key: EpisodeSortKey, dir: number): EpisodeRow[] {
    const parsed = movie.video_files.map((file) => ({ file, ...parseEpisodeNumber(file.filename) }));
    const seasons = new Set(parsed.map((p) => p.season).filter((s) => s !== null));
    const multiSeason = seasons.size > 1;
    const byName = (a: EpisodeRow, b: EpisodeRow) => this.compareText(a.file.filename, b.file.filename);

    // Numero affiche : « 05 », ou « S02E05 » quand la serie compte plusieurs saisons.
    const rows: EpisodeRow[] = parsed.map((p, i) => {
      const ep = String(p.episode ?? i + 1).padStart(2, '0');
      const label = multiSeason && p.season !== null ? `S${String(p.season).padStart(2, '0')}E${ep}` : ep;
      return { ...p, label };
    });

    const compare = (a: EpisodeRow, b: EpisodeRow): number => {
      switch (key) {
        case 'episode': {
          const sa = a.season ?? 0, sb = b.season ?? 0;
          if (sa !== sb) return sa - sb;
          if (a.episode !== b.episode) {
            if (a.episode === null) return 1;
            if (b.episode === null) return -1;
            return a.episode - b.episode;
          }
          return 0;
        }
        case 'filename':
          return byName(a, b);
        case 'video_codec':
          return this.compareText(a.file.video_codec ?? '', b.file.video_codec ?? '');
        case 'resolution':
          return this.pixels(a.file) - this.pixels(b.file);
        case 'size':
          return (a.file.size_bytes || 0) - (b.file.size_bytes || 0);
      }
    };

    // Le nom de fichier sert de critere secondaire (ordre stable, toujours croissant).
    return rows.sort((a, b) => compare(a, b) * dir || byName(a, b));
  }

  private compareText(a: string, b: string): number {
    return a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' });
  }

  private pixels(file: VideoFile): number {
    return (file.width || 0) * (file.height || 0);
  }

  // ---------- Affichage ----------
  posterUrl(movie: Movie): string | null {
    return this.movieService.posterUrl(movie);
  }

  episodeCountLabel(movie: Movie): string {
    const n = movie.video_files.length;
    return `${n} épisode${n > 1 ? 's' : ''}`;
  }

  totalSizeLabel(movie: Movie): string {
    return this.formatSize(movie.video_files.reduce((sum, v) => sum + (v.size_bytes || 0), 0));
  }

  formatSize(bytes: number | undefined): string {
    if (!bytes) return '—';
    const gb = bytes / 1024 / 1024 / 1024;
    return gb >= 1 ? `${gb.toFixed(2)} Go` : `${(bytes / 1024 / 1024).toFixed(0)} Mo`;
  }

  resolutionLabel(file: VideoFile): string {
    return file.width && file.height ? `${file.width}x${file.height}` : '—';
  }

  formatBitrate(bitsPerSec: number | null | undefined): string {
    if (!bitsPerSec) return '—';
    return `${(bitsPerSec / 1000).toFixed(0)} kb/s`;
  }

  // ---------- Fiche detail ----------
  openDetail(movie: Movie): void {
    this.selectedMovie.set(movie);
  }

  closeDetail(): void {
    this.selectedMovie.set(null);
  }

  onMovieUpdated(updated: Movie): void {
    this.series.update((items) => items.map((m) => (m.id === updated.id ? updated : m)));
    this.selectedMovie.set(updated);
    this.fetch();
  }
}
