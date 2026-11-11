import { Component, ElementRef, HostListener, ViewChild, computed, effect, inject, signal } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';

import { APP_NAME, APP_REPOSITORY_URL, APP_VERSION } from '../../config/app-settings';
import { AppDialogService } from '../../services/app-dialog.service';
import { UpdateCheckResult, UpdateService } from '../../services/update.service';
import { markdownToHtml } from '../../utils/markdown';

type UpdateState = 'idle' | 'checking' | 'upToDate' | 'available' | 'error';

/**
 * Fenetre « A propos ». Affichee une seule fois dans AppComponent ; ouverte via
 * AppDialogService (double-clic sur le titre du bandeau, bouton « A propos »
 * de la vue « Outils des bibliotheques »).
 *
 * Le bouton « Verifier les mises a jour » compare APP_VERSION avec le « tag_name » de la
 * derniere release GitHub et affiche les release notes (Markdown) si elle est differente.
 */
@Component({
  selector: 'app-about-dialog',
  standalone: true,
  templateUrl: './about-dialog.component.html',
  styleUrls: ['../dialog-shared.css', './about-dialog.component.css'],
})
export class AboutDialogComponent {
  protected readonly dialogs = inject(AppDialogService);
  private readonly updateService = inject(UpdateService);

  readonly appName = APP_NAME;
  readonly appVersion = APP_VERSION;
  readonly repositoryUrl = APP_REPOSITORY_URL;

  readonly updateState = signal<UpdateState>('idle');
  readonly updateResult = signal<UpdateCheckResult | null>(null);
  readonly updateError = signal('');

  /** Release notes converties de Markdown en HTML (filtre ensuite par le sanitizer Angular). */
  readonly releaseNotesHtml = computed(() => markdownToHtml(this.updateResult()?.releaseNotes));

  readonly publishedDate = computed(() => {
    const iso = this.updateResult()?.publishedAt;
    if (!iso) return '';
    const d = new Date(iso);
    return Number.isNaN(d.getTime()) ? '' : d.toLocaleDateString('fr-FR');
  });

  @ViewChild('aboutOkBtn') private okBtnRef?: ElementRef<HTMLButtonElement>;

  constructor() {
    effect(() => {
      // Place le focus sur le bouton "OK" a l'ouverture de la fenetre
      // et reinitialise le resultat de la derniere verification.
      if (this.dialogs.aboutOpen()) {
        this.resetUpdate();
        setTimeout(() => this.okBtnRef?.nativeElement.focus());
      }
    });
  }

  checkForUpdates(): void {
    if (this.updateState() === 'checking') return;
    this.updateState.set('checking');
    this.updateResult.set(null);
    this.updateError.set('');

    this.updateService.checkForUpdate().subscribe({
      next: (result) => {
        this.updateResult.set(result);
        this.updateState.set(result.updateAvailable ? 'available' : 'upToDate');
      },
      error: (err: unknown) => {
        this.updateError.set(this.describeError(err));
        this.updateState.set('error');
      },
    });
  }

  private resetUpdate(): void {
    this.updateState.set('idle');
    this.updateResult.set(null);
    this.updateError.set('');
  }

  private describeError(err: unknown): string {
    if (err instanceof HttpErrorResponse) {
      if (err.status === 0) {
        return 'Impossible de contacter GitHub. Vérifiez votre connexion Internet.';
      }
      if (err.status === 404) {
        return 'Aucune release publiée sur le dépôt GitHub.';
      }
      if (err.status === 403 || err.status === 429) {
        return 'Limite de requêtes de l’API GitHub atteinte. Réessayez plus tard.';
      }
      return `Erreur GitHub (HTTP ${err.status}).`;
    }
    return err instanceof Error ? err.message : 'Erreur inconnue lors de la vérification.';
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    if (this.dialogs.aboutOpen()) {
      this.dialogs.closeAbout();
    }
  }
}
