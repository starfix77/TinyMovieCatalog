import { Component, effect, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';

import { LibraryService } from '../../services/library.service';
import { SagaService } from '../../services/saga.service';
import { MovieService } from '../../services/movie.service';
import { SagaDetail, SagaListItem } from '../../models/saga.model';
import { Movie } from '../../models/movie.model';
import { MovieDetailComponent } from '../movie-detail/movie-detail.component';

@Component({
  selector: 'app-saga-view',
  standalone: true,
  imports: [CommonModule, MovieDetailComponent],
  templateUrl: './saga-view.component.html',
  styleUrl: './saga-view.component.css',
})
export class SagaViewComponent {
  private readonly libraryService = inject(LibraryService);
  private readonly sagaService = inject(SagaService);
  private readonly movieService = inject(MovieService);

  readonly activeLibraryId = this.libraryService.activeLibraryId;

  sagas = signal<SagaListItem[]>([]);
  loadingSagas = signal(false);

  selectedSagaId = signal<number | null>(null);
  sagaDetail = signal<SagaDetail | null>(null);
  loadingDetail = signal(false);

  selectedMovie = signal<Movie | null>(null);

  constructor() {
    // Recharge la liste des sagas au changement de bibliotheque ou apres un
    // scan (nouvelle saga potentiellement detectee).
    // "allowSignalWrites: true" : necessaire car fetchSagas() ecrit dans des
    // signaux pendant l'execution de l'effect.
    effect(() => {
      this.activeLibraryId();
      this.libraryService.moviesRefreshTick();
      this.fetchSagas();
    }, { allowSignalWrites: true });
  }

  fetchSagas(): void {
    const libId = this.activeLibraryId();
    this.selectedSagaId.set(null);
    this.sagaDetail.set(null);
    if (!libId) {
      this.sagas.set([]);
      return;
    }
    this.loadingSagas.set(true);
    this.sagaService.listSagas(libId).subscribe({
      next: (list) => {
        this.sagas.set(list);
        this.loadingSagas.set(false);
      },
      error: () => this.loadingSagas.set(false),
    });
  }

  sagaPosterUrl(saga: SagaListItem): string | null {
    return this.sagaService.sagaPosterUrl(saga);
  }

  movieEntryPosterUrl(filename: string | null): string | null {
    return this.sagaService.movieEntryPosterUrl(filename);
  }

  selectSaga(saga: SagaListItem): void {
    const libId = this.activeLibraryId();
    if (!libId) return;
    this.selectedSagaId.set(saga.id);
    this.loadingDetail.set(true);
    this.sagaService.getSaga(saga.id, libId).subscribe({
      next: (detail) => {
        this.sagaDetail.set(detail);
        this.loadingDetail.set(false);
      },
      error: () => this.loadingDetail.set(false),
    });
  }

  openMovie(movieId: number | null): void {
    // Les films absents de la bibliotheque (pas de movie_id local) ne
    // peuvent pas ouvrir de fiche detaillee locale.
    if (!movieId) return;
    this.movieService.getMovie(movieId).subscribe((movie) => this.selectedMovie.set(movie));
  }

  closeDetail(): void {
    this.selectedMovie.set(null);
  }

  onMovieUpdated(updated: Movie): void {
    this.selectedMovie.set(updated);
  }
}
