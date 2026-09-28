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

/** Nombre maximum de vignettes rendues dans l'apercu (une seule ligne visible,
 *  le CSS masque ce qui depasse selon la largeur de l'ecran). */
const PREVIEW_LIMIT = 12;

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
  readonly previewLimit = PREVIEW_LIMIT;

  movies = signal<Movie[]>([]);
  loading = signal(false);
  selectedMovie = signal<Movie | null>(null);

  /** Genres actuellement affiches en entier ("Voir tout"). */
  expanded = signal<ReadonlySet<string>>(new Set());

  /** Un film peut appartenir a plusieurs genres ("Action, Science-fiction") :
   *  il apparait alors dans chacune des sections correspondantes.
   *  Seuls les genres presents dans la bibliotheque sont generes ; tri par
   *  nombre de films decroissant, puis ordre alphabetique. */
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
      .sort((a, b) => b.movies.length - a.movies.length || a.name.localeCompare(b.name, 'fr'));
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

  isExpanded(genre: string): boolean {
    return this.expanded().has(genre);
  }

  /** Bascule l'affichage complet d'un genre, sans recharger la vue. */
  toggleExpand(genre: string): void {
    const next = new Set(this.expanded());
    if (next.has(genre)) next.delete(genre);
    else next.add(genre);
    this.expanded.set(next);
  }

  visibleMovies(section: GenreSection): Movie[] {
    return this.isExpanded(section.name) ? section.movies : section.movies.slice(0, PREVIEW_LIMIT);
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
