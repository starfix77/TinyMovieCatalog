import { Component, computed, effect, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';

import { LibraryService } from '../../services/library.service';
import { MovieService } from '../../services/movie.service';
import { NoteService } from '../../services/note.service';
import { Movie } from '../../models/movie.model';
import { NoteListItem } from '../../models/note.model';
import { MovieDetailComponent } from '../movie-detail/movie-detail.component';

/** Vue « Notes » : films / series de la bibliotheque active ayant une note. */
@Component({
  selector: 'app-notes-view',
  standalone: true,
  imports: [CommonModule, MovieDetailComponent],
  templateUrl: './notes-view.component.html',
  styleUrl: './notes-view.component.css',
})
export class NotesViewComponent {
  private readonly libraryService = inject(LibraryService);
  private readonly movieService = inject(MovieService);
  private readonly noteService = inject(NoteService);

  readonly isTv = computed(() => this.libraryService.activeLibrary()?.media_type === 'tv');

  readonly notes = signal<NoteListItem[]>([]);
  readonly loading = signal(false);
  readonly error = signal('');
  readonly openingId = signal<number | null>(null);
  readonly selectedMovie = signal<Movie | null>(null);
  private requestToken = 0;

  constructor() {
    effect(() => {
      const libraryId = this.libraryService.activeLibraryId();
      this.libraryService.moviesRefreshTick();
      this.load(libraryId);
    }, { allowSignalWrites: true });
  }

  private load(libraryId: number | null): void {
    const token = ++this.requestToken;
    if (!libraryId) {
      this.notes.set([]);
      this.loading.set(false);
      return;
    }
    this.loading.set(true);
    this.error.set('');
    this.noteService.listNotes(libraryId).subscribe({
      next: (res) => {
        if (token !== this.requestToken) return;
        this.notes.set(res.items);
        this.loading.set(false);
      },
      error: () => {
        if (token !== this.requestToken) return;
        this.error.set('Impossible de charger les notes.');
        this.loading.set(false);
      },
    });
  }

  private reload(): void {
    this.load(this.libraryService.activeLibraryId());
  }

  /** Bouton « Fiche » : ouvre le dialogue de detail du film / de la serie. */
  openDetail(item: NoteListItem): void {
    if (this.openingId() !== null) return;
    this.openingId.set(item.movie_id);
    this.error.set('');
    this.movieService.getMovie(item.movie_id).subscribe({
      next: (movie) => {
        this.openingId.set(null);
        this.selectedMovie.set(movie);
      },
      error: () => {
        this.openingId.set(null);
        this.error.set('Impossible d’ouvrir la fiche.');
      },
    });
  }

  closeDetail(): void {
    this.selectedMovie.set(null);
  }

  onMovieUpdated(updated: Movie): void {
    this.selectedMovie.set(updated);
    this.reload();
  }

  /** La note a ete modifiee ou supprimee depuis la fiche : rafraichit la liste. */
  onNoteSaved(): void {
    this.reload();
  }

  trackNote(_: number, item: NoteListItem): number {
    return item.movie_id;
  }
}
