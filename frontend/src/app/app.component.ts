import { AfterViewInit, Component, ElementRef, HostListener, NgZone, OnDestroy, ViewChild, computed, effect, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NavigationEnd, Router, RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';

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
export class AppComponent implements AfterViewInit, OnDestroy {
  private readonly router = inject(Router);
  private readonly zone = inject(NgZone);
  private resizeObserver?: ResizeObserver;
  private routerSub?: Subscription;

  @ViewChild('topbar', { static: true }) private topbar!: ElementRef<HTMLElement>;
  @ViewChild('navMeasure', { static: true }) private navMeasure!: ElementRef<HTMLElement>;
  @ViewChild('navSlot', { static: true }) private navSlot!: ElementRef<HTMLElement>;
  /** true quand la bibliotheque active est de type "Series TV". */
  readonly isTv = computed(() => this.libraryService.activeLibrary()?.media_type === 'tv');

  isDarkMode = false;
  sidebarCollapsed = false;
  /** true quand la largeur disponible ne permet pas d'afficher tous les liens : passage en menu burger. */
  compactNav = false;
  menuOpen = false;

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

  ngAfterViewInit(): void {
    this.resizeObserver = new ResizeObserver(() => this.zone.run(() => this.updateNavLayout()));
    this.resizeObserver.observe(this.topbar.nativeElement);
    this.resizeObserver.observe(this.navMeasure.nativeElement);
    this.routerSub = this.router.events
      .pipe(filter((event) => event instanceof NavigationEnd))
      .subscribe(() => this.closeMenu());
  }

  ngOnDestroy(): void {
    this.resizeObserver?.disconnect();
    this.routerSub?.unsubscribe();
  }

  toggleMenu(): void {
    this.menuOpen = !this.menuOpen;
  }

  closeMenu(): void {
    this.menuOpen = false;
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (this.menuOpen && !this.navSlot.nativeElement.contains(event.target as Node)) {
      this.closeMenu();
    }
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.closeMenu();
  }

  /**
   * Compare la largeur necessaire aux liens (mesuree sur un clone invisible)
   * a la place restante dans le bandeau une fois les autres elements places.
   */
  private updateNavLayout(): void {
    const topbar = this.topbar.nativeElement;
    const style = getComputedStyle(topbar);
    const gap = parseFloat(style.columnGap) || 0;
    const inner = topbar.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);

    let othersWidth = 0;
    let othersCount = 0;
    for (const child of Array.from(topbar.children) as HTMLElement[]) {
      if (child.hasAttribute('data-nav-ignore') || child.hasAttribute('data-nav-slot')) {
        continue;
      }
      // Observe aussi les elements voisins (nom de bibliotheque, bouton de theme...).
      this.resizeObserver?.observe(child);
      othersWidth += child.getBoundingClientRect().width;
      othersCount++;
    }

    const available = inner - othersWidth - gap * othersCount;
    const needed = Math.ceil(this.navMeasure.nativeElement.getBoundingClientRect().width);
    const compact = needed > available;

    if (compact !== this.compactNav) {
      this.compactNav = compact;
      if (!compact) {
        this.menuOpen = false;
      }
    }
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
