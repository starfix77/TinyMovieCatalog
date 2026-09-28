import { Component, ElementRef, HostListener, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, debounceTime, distinctUntilChanged, switchMap, of } from 'rxjs';

import { LibraryService } from '../../services/library.service';
import { ActorService } from '../../services/actor.service';
import { MovieService } from '../../services/movie.service';
import { ActorFilmography, ActorFilmographyEntry, ActorSearchResult } from '../../models/actor.model';
import { Movie } from '../../models/movie.model';
import { MovieDetailComponent } from '../movie-detail/movie-detail.component';

/** Segment de nom d'acteur, utilise pour mettre en gras la partie saisie
 *  dans la liste d'autocompletion (sans passer par [innerHTML]). */
interface NameSegment {
  text: string;
  bold: boolean;
}

@Component({
  selector: 'app-actor-view',
  standalone: true,
  imports: [CommonModule, FormsModule, MovieDetailComponent],
  templateUrl: './actor-view.component.html',
  styleUrl: './actor-view.component.css',
})
export class ActorViewComponent {
  private readonly libraryService = inject(LibraryService);
  private readonly actorService = inject(ActorService);
  private readonly movieService = inject(MovieService);
  private readonly host = inject(ElementRef<HTMLElement>);

  readonly activeLibraryId = this.libraryService.activeLibraryId;

  // Nombre minimum de caracteres avant de declencher la recherche (doit
  // correspondre a MIN_QUERY_LENGTH cote backend).
  readonly minQueryLength = 2;

  query = '';
  private queryChanged = new Subject<string>();

  suggestions = signal<ActorSearchResult[]>([]);
  suggestionsOpen = signal(false);
  searchingSuggestions = signal(false);

  selectedActor = signal<string | null>(null);
  filmography = signal<ActorFilmography | null>(null);
  loadingFilmography = signal(false);
  filmographyError = signal<string | null>(null);

  selectedMovie = signal<Movie | null>(null);

  // Case a cocher "affiche uniquement les films de la bibliotheque" (cochee
  // par defaut) : filtre l'affichage de la filmographie cote client, sans
  // nouvel appel serveur (les donnees completes sont deja recuperees).
  onlyLibraryMovies = signal(true);

  toggleOnlyLibraryMovies(checked: boolean): void {
    this.onlyLibraryMovies.set(checked);
  }

  /** Films a afficher dans la grille, filtres selon la case a cocher. */
  visibleMovies(filmo: ActorFilmography): ActorFilmographyEntry[] {
    return this.onlyLibraryMovies() ? filmo.movies.filter((m) => m.in_library) : filmo.movies;
  }

  constructor() {
    this.queryChanged
      .pipe(
        debounceTime(220),
        distinctUntilChanged(),
        switchMap((q) => {
          const libId = this.activeLibraryId();
          if (!libId || q.trim().length < this.minQueryLength) {
            return of<ActorSearchResult[]>([]);
          }
          this.searchingSuggestions.set(true);
          return this.actorService.searchActors(libId, q.trim());
        })
      )
      .subscribe({
        next: (results) => {
          this.suggestions.set(results);
          this.suggestionsOpen.set(true);
          this.searchingSuggestions.set(false);
        },
        error: () => this.searchingSuggestions.set(false),
      });
  }

  onQueryInput(): void {
    this.queryChanged.next(this.query);
  }

  onQueryFocus(): void {
    if (this.suggestions().length > 0) {
      this.suggestionsOpen.set(true);
    }
  }

  // Ferme la liste de suggestions au clic en dehors du composant.
  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (!this.host.nativeElement.contains(event.target as Node)) {
      this.suggestionsOpen.set(false);
    }
  }

  /** Decoupe le nom d'un acteur en segments {text, bold} autour du fragment
   *  saisi par l'utilisateur, pour un affichage "Google suggest". */
  highlightSegments(name: string): NameSegment[] {
    const q = this.query.trim();
    if (!q) return [{ text: name, bold: false }];

    const normalize = (s: string) => s.toLocaleLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g, '');
    const normName = normalize(name);
    const normQuery = normalize(q);
    const idx = normName.indexOf(normQuery);
    if (idx === -1) return [{ text: name, bold: false }];

    const segments: NameSegment[] = [];
    if (idx > 0) segments.push({ text: name.slice(0, idx), bold: false });
    segments.push({ text: name.slice(idx, idx + q.length), bold: true });
    if (idx + q.length < name.length) segments.push({ text: name.slice(idx + q.length), bold: false });
    return segments;
  }

  selectActor(actor: ActorSearchResult): void {
    const libId = this.activeLibraryId();
    if (!libId) return;

    this.query = actor.name;
    this.selectedActor.set(actor.name);
    this.suggestionsOpen.set(false);
    this.suggestions.set([]);

    this.loadingFilmography.set(true);
    this.filmographyError.set(null);
    this.filmography.set(null);

    this.actorService.getFilmography(libId, actor.name).subscribe({
      next: (data) => {
        this.filmography.set(data);
        this.loadingFilmography.set(false);
      },
      error: () => {
        this.filmographyError.set("Impossible de recuperer la filmographie de cet acteur.");
        this.loadingFilmography.set(false);
      },
    });
  }

  posterUrl(filename: string | null): string | null {
    return this.actorService.posterUrl(filename);
  }

  openMovie(movieId: number | null): void {
    // Les films absents de la bibliotheque n'ont pas de fiche locale.
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
