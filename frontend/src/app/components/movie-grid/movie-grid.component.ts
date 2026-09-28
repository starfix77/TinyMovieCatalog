import { Component, effect, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { debounceTime, distinctUntilChanged, Subject } from 'rxjs';

import { LibraryService } from '../../services/library.service';
import { MovieService } from '../../services/movie.service';
import { Movie } from '../../models/movie.model';
import { MovieDetailComponent } from '../movie-detail/movie-detail.component';

@Component({
  selector: 'app-movie-grid',
  standalone: true,
  imports: [CommonModule, FormsModule, MovieDetailComponent],
  templateUrl: './movie-grid.component.html',
  styleUrl: './movie-grid.component.css',
})
export class MovieGridComponent {
  private readonly libraryService = inject(LibraryService);
  private readonly movieService = inject(MovieService);

  readonly activeLibraryId = this.libraryService.activeLibraryId;

  search = '';
  private searchChanged = new Subject<string>();

  movies = signal<Movie[]>([]);
  loading = signal(false);
  selectedMovie = signal<Movie | null>(null);

  constructor() {
    this.searchChanged.pipe(debounceTime(250), distinctUntilChanged()).subscribe(() => this.fetch());

    // Recharge la liste des films a chaque changement de bibliotheque active.
    // "allowSignalWrites: true" est necessaire car fetch() ecrit dans les
    // signaux loading/movies pendant l'execution de l'effect (sinon Angular
    // ignore silencieusement l'ecriture et la vue ne se met jamais a jour).
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
      this.movies.set([]);
      return;
    }
    this.loading.set(true);
    this.movieService.listMovies(libId, this.search || undefined, 'title', 'asc').subscribe({
      next: (page) => {
        this.movies.set(page.items);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
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
    // Met a jour immediatement la grille, puis recharge depuis la DB pour
    // resynchroniser toutes les colonnes et la vignette apres le remplacement.
    this.movies.update(items => items.map(movie => movie.id === updated.id ? updated : movie));
    this.selectedMovie.set(updated);
    this.fetch();
  }
}
