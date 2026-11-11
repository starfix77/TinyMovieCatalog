import { Component, ElementRef, HostListener, ViewChild, effect, inject } from '@angular/core';

import { APP_NAME, APP_REPOSITORY_URL, APP_VERSION } from '../../config/app-settings';
import { AppDialogService } from '../../services/app-dialog.service';

/**
 * Fenetre « A propos ». Affichee une seule fois dans AppComponent ; ouverte via
 * AppDialogService (double-clic sur le titre du bandeau, bouton « A propos »
 * de la vue « Outils des bibliotheques »).
 */
@Component({
  selector: 'app-about-dialog',
  standalone: true,
  templateUrl: './about-dialog.component.html',
  styleUrls: ['../dialog-shared.css', './about-dialog.component.css'],
})
export class AboutDialogComponent {
  protected readonly dialogs = inject(AppDialogService);

  readonly appName = APP_NAME;
  readonly appVersion = APP_VERSION;
  readonly repositoryUrl = APP_REPOSITORY_URL;

  @ViewChild('aboutOkBtn') private okBtnRef?: ElementRef<HTMLButtonElement>;

  constructor() {
    effect(() => {
      // Place le focus sur le bouton "OK" a l'ouverture de la fenetre.
      if (this.dialogs.aboutOpen()) {
        setTimeout(() => this.okBtnRef?.nativeElement.focus());
      }
    });
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    if (this.dialogs.aboutOpen()) {
      this.dialogs.closeAbout();
    }
  }
}
