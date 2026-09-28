import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';

import { LibrarySelectorComponent } from './components/library-selector/library-selector.component';
import { LibraryService } from './services/library.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive, LibrarySelectorComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent {
  isDarkMode = false;
  sidebarCollapsed = false;

  constructor(public readonly libraryService: LibraryService) {
    const savedTheme = localStorage.getItem('tinymoviecatalog-theme');
    this.isDarkMode = savedTheme ? savedTheme === 'dark' : false;
    this.applyTheme();

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
