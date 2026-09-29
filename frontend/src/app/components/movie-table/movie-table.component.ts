import { Component, effect, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { debounceTime, distinctUntilChanged, Subject } from 'rxjs';

import { LibraryService } from '../../services/library.service';
import { MovieService } from '../../services/movie.service';
import { Movie, SortDir, SortField } from '../../models/movie.model';
import { MovieDetailComponent } from '../movie-detail/movie-detail.component';

interface ColumnDef {
  key: SortField;
  label: string;
  sortable: true;
}

@Component({
  selector: 'app-movie-table',
  standalone: true,
  imports: [CommonModule, FormsModule, MovieDetailComponent],
  templateUrl: './movie-table.component.html',
  styleUrl: './movie-table.component.css',
})
export class MovieTableComponent {
  private readonly libraryService = inject(LibraryService);
  private readonly movieService = inject(MovieService);

  readonly activeLibraryId = this.libraryService.activeLibraryId;

  readonly columns: ColumnDef[] = [
    { key: 'title', label: 'Nom du film (annee)', sortable: true },
    { key: 'filename', label: 'Fichier video', sortable: true },
    { key: 'video_codec', label: 'Encodage', sortable: true },
    { key: 'resolution', label: 'Resolution', sortable: true },
    { key: 'size', label: 'Taille', sortable: true },
  ];

  search = '';
  private searchChanged = new Subject<string>();

  sortBy = signal<SortField>('title');
  sortDir = signal<SortDir>('asc');

  movies = signal<Movie[]>([]);
  loading = signal(false);
  selectedMovie = signal<Movie | null>(null);

  constructor() {
    this.searchChanged.pipe(debounceTime(250), distinctUntilChanged()).subscribe(() => this.fetch());

    // "allowSignalWrites: true" est necessaire car fetch() ecrit dans les
    // signaux loading/movies pendant l'execution de l'effect (sinon Angular
    // ignore silencieusement l'ecriture et la vue ne se met jamais a jour).
    effect(() => {
      this.activeLibraryId();
      this.libraryService.moviesRefreshTick();
      this.sortBy();
      this.sortDir();
      this.fetch();
    }, { allowSignalWrites: true });
  }

  onSearchInput(): void {
    this.searchChanged.next(this.search);
  }

  toggleSort(field: SortField): void {
    if (this.sortBy() === field) {
      this.sortDir.set(this.sortDir() === 'asc' ? 'desc' : 'asc');
    } else {
      this.sortBy.set(field);
      this.sortDir.set('asc');
    }
  }

  sortIcon(field: SortField): string {
    if (this.sortBy() !== field) return '';
    return this.sortDir() === 'asc' ? '▲' : '▼';
  }

  fetch(): void {
    const libId = this.activeLibraryId();
    if (!libId) {
      this.movies.set([]);
      return;
    }
    this.loading.set(true);
    this.movieService.listMovies(libId, this.search || undefined, this.sortBy(), this.sortDir()).subscribe({
      next: (page) => {
        this.movies.set(page.items);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  openDetail(movie: Movie): void {
    this.selectedMovie.set(movie);
  }

  closeDetail(): void {
    this.selectedMovie.set(null);
  }

  onMovieUpdated(updated: Movie): void {
    // Meme comportement que la vue Films : mise a jour immediate de la ligne,
    // puis rechargement depuis la DB pour resynchroniser toutes les colonnes.
    this.movies.update(items => items.map(movie => movie.id === updated.id ? updated : movie));
    this.selectedMovie.set(updated);
    this.fetch();
  }

  mainVideo(movie: Movie) {
    return movie.video_files[0] ?? null;
  }

  formatSize(bytes: number | undefined): string {
    if (!bytes) return '—';
    const gb = bytes / 1024 / 1024 / 1024;
    return gb >= 1 ? `${gb.toFixed(2)} Go` : `${(bytes / 1024 / 1024).toFixed(0)} Mo`;
  }

  resolutionLabel(movie: Movie): string {
    const v = this.mainVideo(movie);
    if (!v || !v.width || !v.height) return '—';
    return `${v.width}x${v.height}`;
  }

  formatBitrate(bitsPerSec: number | null | undefined): string {
    if (!bitsPerSec) return '—';
    return `${(bitsPerSec / 1000).toFixed(0)} kb/s`;
  }
}
