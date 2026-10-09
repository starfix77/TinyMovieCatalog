import { Component, EventEmitter, Input, Output, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { MovieService } from '../../services/movie.service';
import { CastMember, Movie, MoviePoster, TmdbCandidate, TmdbLanguage } from '../../models/movie.model';

@Component({
  selector: 'app-movie-detail',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './movie-detail.component.html',
  styleUrl: './movie-detail.component.css',
})
export class MovieDetailComponent {
  private readonly movieService = inject(MovieService);

  @Input({ required: true }) movie!: Movie;
  @Output() close = new EventEmitter<void>();
  @Output() movieUpdated = new EventEmitter<Movie>();

  editing = false;
  loadingCandidates = false;
  saving = false;
  candidates: TmdbCandidate[] = [];
  errorMessage = '';
  selectedCandidateId: number | null = null;

  get posterUrl(): string | null {
    return this.movieService.posterUrl(this.movie);
  }

  get cast(): CastMember[] {
    if (!this.movie.cast) return [];
    try {
      return JSON.parse(this.movie.cast) as CastMember[];
    } catch {
      return [];
    }
  }

  get mainVideoFile() {
    return this.movie.video_files[0] ?? null;
  }

  formatSize(bytes: number): string {
    if (!bytes) return '—';
    const gb = bytes / 1024 / 1024 / 1024;
    return gb >= 1 ? `${gb.toFixed(2)} Go` : `${(bytes / 1024 / 1024).toFixed(0)} Mo`;
  }

  formatDuration(seconds: number | null): string {
    if (!seconds) return '—';
    const h = Math.floor(seconds / 3600);
    const m = Math.round((seconds % 3600) / 60);
    return `${h} h ${m.toString().padStart(2, '0')} min`;
  }

  formatBitrate(bitsPerSec: number | null): string {
    if (!bitsPerSec) return '—';
    return `${(bitsPerSec / 1000).toFixed(0)} kb/s`;
  }

  openMetadataEditor(): void {
    this.editing = true;
    this.loadingCandidates = true;
    this.errorMessage = '';
    this.candidates = [];
    this.selectedCandidateId = null;
    this.movieService.searchTmdb(this.movie.id).subscribe({
      next: (candidates) => {
        this.candidates = candidates;
        this.loadingCandidates = false;
        if (!candidates.length) this.errorMessage = 'Aucun film TMDb correspondant n’a été trouvé.';
      },
      error: (error) => {
        this.loadingCandidates = false;
        this.errorMessage = error?.error?.detail || 'Impossible de rechercher les films sur TMDb.';
      },
    });
  }

  cancelMetadataEdit(): void {
    if (!this.saving) this.editing = false;
  }

  selectCandidate(candidate: TmdbCandidate): void {
    this.selectedCandidateId = candidate.tmdb_id;
  }

  candidatePosterUrl(candidate: TmdbCandidate): string | null {
    return this.movieService.tmdbPosterUrl(candidate.poster_path);
  }

  saveMetadata(): void {
    if (this.selectedCandidateId === null || this.saving) return;
    const movieId = this.movie.id;
    const tmdbId = this.selectedCandidateId;
    this.saving = true;
    this.errorMessage = '';
    this.movieService.updateMetadata(movieId, tmdbId).subscribe({
      next: () => {
        // Relit le film depuis l'API apres le PUT afin de garantir que
        // l'affichage Angular correspond bien aux donnees persistées en DB.
        this.movieService.getMovie(movieId).subscribe({
          next: (updated) => {
            this.movie = updated;
            this.saving = false;
            this.editing = false;
            this.movieUpdated.emit(updated);
          },
          error: (error) => {
            this.saving = false;
            this.errorMessage = error?.error?.detail || 'Les informations ont été enregistrées, mais leur relecture a échoué.';
          },
        });
      },
      error: (error) => {
        this.saving = false;
        this.errorMessage = error?.error?.detail || 'Impossible de mettre à jour les informations du film.';
      },
    });
  }

  // ---------- Lecture du film (ffplay) ----------
  playing = false;
  playError = '';

  playMovieFile(): void {
    if (this.playing) return;
    this.playing = true;
    this.playError = '';
    this.movieService.playMovie(this.movie.id).subscribe({
      next: () => {
        this.playing = false;
      },
      error: (error) => {
        this.playing = false;
        this.playError = error?.error?.detail || 'Impossible de lancer la lecture du film.';
      },
    });
  }

  // ---------- Changement de pochette ----------
  posterDialogOpen = false;
  languages: { code: string; label: string; search: string }[] = [];
  loadingLanguages = false;
  languageQuery = '';
  selectedLanguageCode = '';
  suggestionsOpen = false;
  activeSuggestion = -1;
  searchingPosters = false;
  posterSearched = false;
  posters: MoviePoster[] = [];
  selectedPosterPath: string | null = null;
  applyingPoster = false;
  posterError = '';
  private defaultLanguage = '';

  get filteredLanguages() {
    const q = this.normalize(this.languageQuery);
    const list = !q || this.languageQuery === this.labelOf(this.selectedLanguageCode)
      ? this.languages
      : this.languages.filter((l) => l.search.includes(q));
    return list;
  }

  openPosterDialog(): void {
    this.posterDialogOpen = true;
    this.posters = [];
    this.posterSearched = false;
    this.selectedPosterPath = null;
    this.posterError = '';
    if (this.languages.length) {
      this.setLanguage(this.defaultLanguage);
      return;
    }
    this.loadingLanguages = true;
    this.movieService.getTmdbLanguages().subscribe({
      next: (res) => {
        this.defaultLanguage = res.default;
        this.languages = res.languages
          .map((l) => this.toOption(l))
          .sort((a, b) => a.label.localeCompare(b.label, 'fr'));
        this.loadingLanguages = false;
        this.setLanguage(res.default);
      },
      error: (error) => {
        this.loadingLanguages = false;
        this.posterError = error?.error?.detail || 'Impossible de récupérer la liste des langues TMDb.';
      },
    });
  }

  closePosterDialog(): void {
    if (!this.applyingPoster) this.posterDialogOpen = false;
  }

  private toOption(l: TmdbLanguage) {
    const iso = l.code.split('-')[0] ?? l.code;
    let name = l.native_name || l.english_name;
    try {
      const dn = new Intl.DisplayNames(['fr'], { type: 'language' }).of(iso);
      if (dn && dn !== iso) name = dn.charAt(0).toUpperCase() + dn.slice(1);
    } catch {
      name = l.english_name;
    }
    const label = `${name} (${l.code})`;
    return {
      code: l.code,
      label,
      search: this.normalize(`${label} ${l.english_name} ${l.native_name}`),
    };
  }

  private labelOf(code: string): string {
    return this.languages.find((l) => l.code === code)?.label ?? '';
  }

  private normalize(text: string): string {
    return (text || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  }

  private setLanguage(code: string): void {
    const found = this.languages.find((l) => l.code === code);
    this.selectedLanguageCode = found ? found.code : '';
    this.languageQuery = found ? found.label : code;
    this.suggestionsOpen = false;
    this.activeSuggestion = -1;
  }

  onLanguageInput(): void {
    this.selectedLanguageCode = '';
    this.suggestionsOpen = true;
    this.activeSuggestion = this.filteredLanguages.length ? 0 : -1;
  }

  onLanguageKey(event: KeyboardEvent): void {
    const list = this.filteredLanguages;
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      this.suggestionsOpen = true;
      this.activeSuggestion = Math.min(this.activeSuggestion + 1, list.length - 1);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      this.activeSuggestion = Math.max(this.activeSuggestion - 1, 0);
    } else if (event.key === 'Enter') {
      event.preventDefault();
      const active = list[this.activeSuggestion];
      if (this.suggestionsOpen && active) {
        this.setLanguage(active.code);
      } else {
        this.searchPosters();
      }
    } else if (event.key === 'Escape' && this.suggestionsOpen) {
      event.stopPropagation();
      this.suggestionsOpen = false;
    }
  }

  chooseLanguage(code: string): void {
    this.setLanguage(code);
  }

  closeSuggestionsLater(): void {
    // Laisse le temps au clic sur une suggestion d'être pris en compte.
    setTimeout(() => {
      this.suggestionsOpen = false;
      if (!this.selectedLanguageCode) {
        const exact = this.languages.find((l) => l.label === this.languageQuery);
        if (exact) this.selectedLanguageCode = exact.code;
      }
    }, 150);
  }

  searchPosters(): void {
    if (this.searchingPosters || this.applyingPoster) return;
    if (!this.selectedLanguageCode) {
      this.posterError = 'Choisissez une langue dans la liste.';
      return;
    }
    this.searchingPosters = true;
    this.posterError = '';
    this.posters = [];
    this.selectedPosterPath = null;
    this.movieService.searchPosters(this.movie.id, this.selectedLanguageCode).subscribe({
      next: (posters) => {
        this.posters = posters;
        this.posterSearched = true;
        this.searchingPosters = false;
      },
      error: (error) => {
        this.searchingPosters = false;
        this.posterSearched = false;
        this.posterError = error?.error?.detail || 'Impossible de rechercher les pochettes.';
      },
    });
  }

  posterThumbUrl(poster: MoviePoster): string {
    return this.movieService.tmdbThumbUrl(poster.file_path);
  }

  selectPoster(poster: MoviePoster): void {
    this.selectedPosterPath = poster.file_path;
  }

  applyPoster(poster: MoviePoster): void {
    if (this.applyingPoster) return;
    this.selectedPosterPath = poster.file_path;
    this.applyingPoster = true;
    this.posterError = '';
    this.movieService.changePoster(this.movie.id, poster.file_path).subscribe({
      next: (updated) => {
        this.movie = updated;
        this.applyingPoster = false;
        this.posterDialogOpen = false;
        this.movieUpdated.emit(updated);
      },
      error: (error) => {
        this.applyingPoster = false;
        this.posterError = error?.error?.detail || 'Impossible de remplacer la pochette.';
      },
    });
  }

  trackPoster(_: number, poster: MoviePoster): string {
    return poster.file_path;
  }

  trackCandidate(_: number, candidate: TmdbCandidate): number {
    return candidate.tmdb_id;
  }

  onBackdropClick(event: MouseEvent): void {
    if (event.target === event.currentTarget) this.close.emit();
  }
}
