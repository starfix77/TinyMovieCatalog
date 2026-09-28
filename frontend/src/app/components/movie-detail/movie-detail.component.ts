import { Component, EventEmitter, Input, Output, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { MovieService } from '../../services/movie.service';
import { CastMember, Movie, TmdbCandidate } from '../../models/movie.model';

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

  trackCandidate(_: number, candidate: TmdbCandidate): number {
    return candidate.tmdb_id;
  }

  onBackdropClick(event: MouseEvent): void {
    if (event.target === event.currentTarget) this.close.emit();
  }
}
