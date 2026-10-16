import { Component, computed, effect, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';

import { LibraryService } from '../../services/library.service';
import { MovieService } from '../../services/movie.service';
import { Movie } from '../../models/movie.model';
import { MovieDetailComponent } from '../movie-detail/movie-detail.component';

interface GenreSection {
  name: string;
  movies: Movie[];
}

@Component({
  selector: 'app-genre-view',
  standalone: true,
  imports: [CommonModule, MovieDetailComponent],
  templateUrl: './genre-view.component.html',
  styleUrl: './genre-view.component.css',
})
export class GenreViewComponent {
  private readonly libraryService = inject(LibraryService);
  private readonly movieService = inject(MovieService);

  readonly activeLibraryId = this.libraryService.activeLibraryId;

  movies = signal<Movie[]>([]);
  loading = signal(false);
  selectedMovie = signal<Movie | null>(null);

  /** Genres actuellement reduits (par defaut, toutes les sections sont developpees,
   *  comme dans l'onglet Doublons). */
  collapsed = signal<ReadonlySet<string>>(new Set());

  /** Un film peut appartenir a plusieurs genres ("Action, Science-fiction") :
   *  il apparait alors dans chacune des sections correspondantes.
   *  Seuls les genres presents dans la bibliotheque sont generes ; tri par
   *  ordre alphabetique du nom de genre. */
  sections = computed<GenreSection[]>(() => {
    const byGenre = new Map<string, Movie[]>();
    for (const movie of this.movies()) {
      const genres = new Set(
        (movie.genres ?? '').split(',').map(g => g.trim()).filter(g => g.length > 0)
      );
      for (const genre of genres) {
        const list = byGenre.get(genre);
        if (list) list.push(movie);
        else byGenre.set(genre, [movie]);
      }
    }
    return [...byGenre.entries()]
      .map(([name, list]) => ({
        name,
        movies: [...list].sort((a, b) => a.title.localeCompare(b.title, 'fr', { sensitivity: 'base' })),
      }))
      .sort((a, b) => a.name.localeCompare(b.name, 'fr', { sensitivity: 'base' }));
  });

  constructor() {
    effect(() => {
      this.activeLibraryId();
      this.libraryService.moviesRefreshTick();
      this.fetch();
    }, { allowSignalWrites: true });
  }

  fetch(): void {
    const libId = this.activeLibraryId();
    if (!libId) {
      this.movies.set([]);
      return;
    }
    this.loading.set(true);
    this.movieService.listMovies(libId, undefined, 'title', 'asc').subscribe({
      next: (page) => {
        this.movies.set(page.items);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  isCollapsed(genre: string): boolean {
    return this.collapsed().has(genre);
  }

  /** Vrai quand toutes les sections sont reduites. */
  allCollapsed = computed(() => {
    const list = this.sections();
    const collapsed = this.collapsed();
    return list.length > 0 && list.every(s => collapsed.has(s.name));
  });

  /** Reduit toutes les sections, ou les developpe toutes si elles sont deja reduites. */
  toggleAll(): void {
    if (this.allCollapsed()) this.collapsed.set(new Set());
    else this.collapsed.set(new Set(this.sections().map(s => s.name)));
  }

  /** Developpe / reduit une section de genre, sans recharger la vue. */
  toggle(genre: string): void {
    const next = new Set(this.collapsed());
    if (next.has(genre)) next.delete(genre);
    else next.add(genre);
    this.collapsed.set(next);
  }

  posterUrl(movie: Movie): string | null {
    return this.movieService.posterUrl(movie);
  }

  openDetail(movie: Movie): void {
    this.selectedMovie.set(movie);
  }

  closeDetail(): void {
    this.selectedMovie.set(null);
  }

  onMovieUpdated(updated: Movie): void {
    this.movies.update(items => items.map(m => (m.id === updated.id ? updated : m)));
    this.selectedMovie.set(updated);
    this.fetch();
  }
}
