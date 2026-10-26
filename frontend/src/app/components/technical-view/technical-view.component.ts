import { Component, computed, inject } from '@angular/core';

import { LibraryService } from '../../services/library.service';
import { MovieTableComponent } from '../movie-table/movie-table.component';
import { MovieDetailTvComponent } from '../movie-detail-tv/movie-detail-tv.component';

/** Page « Détail technique » : aiguille vers la vue Films ou la vue Séries TV
 *  selon le type de la bibliothèque active. */
@Component({
  selector: 'app-technical-view',
  standalone: true,
  imports: [MovieTableComponent, MovieDetailTvComponent],
  template: `
    @if (isTv()) {
      <app-movie-detail-tv></app-movie-detail-tv>
    } @else {
      <app-movie-table></app-movie-table>
    }
  `,
})
export class TechnicalViewComponent {
  private readonly libraryService = inject(LibraryService);
  readonly isTv = computed(() => this.libraryService.activeLibrary()?.media_type === 'tv');
}
