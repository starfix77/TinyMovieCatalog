import { Component, ElementRef, HostListener, ViewChild, effect, inject, signal, untracked } from '@angular/core';

import { AppDialogService } from '../../services/app-dialog.service';
import { SettingsService } from '../../services/settings.service';
import { AppSettings, SettingSource } from '../../models/settings.model';

/**
 * Boite de dialogue « Configuration » : affiche, en lecture seule, tous les
 * parametres du fichier backend/.env (valeurs chargees au demarrage du backend).
 * Les secrets (ex. TMDB_API_KEY) sont masques par le backend.
 */
@Component({
  selector: 'app-settings-dialog',
  standalone: true,
  templateUrl: './settings-dialog.component.html',
  styleUrls: ['../dialog-shared.css', './settings-dialog.component.css'],
})
export class SettingsDialogComponent {
  protected readonly dialogs = inject(AppDialogService);
  private readonly settingsService = inject(SettingsService);

  readonly settings = signal<AppSettings | null>(null);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);

  @ViewChild('settingsOkBtn') private okBtnRef?: ElementRef<HTMLButtonElement>;

  constructor() {
    effect(() => {
      if (this.dialogs.settingsOpen()) {
        // Recharge a chaque ouverture : le backend a pu etre redemarre entre-temps.
        untracked(() => this.load());
        setTimeout(() => this.okBtnRef?.nativeElement.focus());
      }
    });
  }

  private load(): void {
    this.loading.set(true);
    this.error.set(null);
    this.settingsService.getSettings().subscribe({
      next: (data) => {
        this.settings.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.settings.set(null);
        this.error.set('Impossible de lire la configuration : le backend ne répond pas.');
        this.loading.set(false);
      },
    });
  }

  sourceLabel(source: SettingSource): string {
    switch (source) {
      case 'env_file':
        return 'Fichier .env';
      case 'environment':
        return "Variable d'environnement";
      default:
        return 'Valeur par défaut';
    }
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    if (this.dialogs.settingsOpen()) {
      this.dialogs.closeSettings();
    }
  }
}
