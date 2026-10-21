import { Component, computed, effect, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';

import { LibrarySelectorComponent } from './components/library-selector/library-selector.component';
import { LibraryService } from './services/library.service';
import { MediaTypeIconComponent } from './components/media-type-icon/media-type-icon.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive, LibrarySelectorComponent, MediaTypeIconComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent {
  private readonly router = inject(Router);
  /** true quand la bibliotheque active est de type "Series TV". */
  readonly isTv = computed(() => this.libraryService.activeLibrary()?.media_type === 'tv');

  isDarkMode = false;
  sidebarCollapsed = false;

  constructor(public readonly libraryService: LibraryService) {
    const savedTheme = localStorage.getItem('tinymoviecatalog-theme');
    this.isDarkMode = savedTheme ? savedTheme === 'dark' : false;
    this.applyTheme();

    // La page "Saga" n'existe pas pour les series : retour a l'accueil si on s'y trouve.
    effect(() => {
      if (this.isTv() && this.router.url.startsWith('/sagas')) {
        this.router.navigateByUrl('/');
      }
    });

    const savedSidebar = localStorage.getItem('tinymoviecatalog-sidebar-collapsed');
    this.sidebarCollapsed = savedSidebar === 'true';
  }

  toggleTheme(): void {
    this.isDarkMode = !this.isDarkMode;
    localStorage.setItem('tinymoviecatalog-theme', this.isDarkMode ? 'dark' : 'light');
    this.applyTheme();
  }

  toggleSidebar(): void {
    this.sidebarCollapsed = !this.sidebarCollapsed;
    localStorage.setItem('tinymoviecatalog-sidebar-collapsed', String(this.sidebarCollapsed));
  }

  private applyTheme(): void {
    document.documentElement.dataset['theme'] = this.isDarkMode ? 'dark' : 'light';
  }
}
