import { Injectable, signal } from '@angular/core';

/**
 * Etat d'ouverture des boites de dialogue de l'application (« A propos » et
 * « Configuration »). Les dialogues sont affiches une seule fois, dans
 * AppComponent ; n'importe quel composant peut les ouvrir via ce service
 * (titre du bandeau de gauche, vue « Outils des bibliotheques »...).
 */
@Injectable({ providedIn: 'root' })
export class AppDialogService {
  readonly aboutOpen = signal(false);
  readonly settingsOpen = signal(false);

  openAbout(): void {
    this.aboutOpen.set(true);
  }

  closeAbout(): void {
    this.aboutOpen.set(false);
  }

  openSettings(): void {
    this.settingsOpen.set(true);
  }

  closeSettings(): void {
    this.settingsOpen.set(false);
  }
}
