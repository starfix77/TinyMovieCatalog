import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

import { MediaType } from '../../models/library.model';

/**
 * Icone du type de bibliotheque : pellicule de cinema (Films) ou television
 * (Series TV). Dessinee en traits avec currentColor : elle suit donc la couleur
 * du texte et s'adapte automatiquement aux themes clair et sombre.
 */
@Component({
  selector: 'app-media-type-icon',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <svg class="media-icon" [attr.width]="size" [attr.height]="size" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"
         role="img" [attr.aria-label]="label">
      <title>{{ label }}</title>
      @if (type === 'tv') {
        <rect x="3" y="7" width="18" height="13" rx="2"></rect>
        <path d="M8 3l4 4 4-4"></path>
      } @else {
        <rect x="3" y="3" width="18" height="18" rx="2"></rect>
        <path d="M7 3v18M17 3v18M3 8h4M3 12h4M3 16h4M17 8h4M17 12h4M17 16h4"></path>
      }
    </svg>
  `,
  styles: [`
    :host { display: inline-flex; align-items: center; flex-shrink: 0; }
    .media-icon { display: block; }
  `],
})
export class MediaTypeIconComponent {
  @Input() type: MediaType | null | undefined = 'movie';
  @Input() size = 16;

  get label(): string {
    return this.type === 'tv' ? 'Bibliothèque de séries TV' : 'Bibliothèque de films';
  }
}
