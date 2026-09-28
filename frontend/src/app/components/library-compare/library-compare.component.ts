import { Component, ElementRef, HostListener, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { LibraryService } from '../../services/library.service';
import { CompareDepth, CompareMode, CompareResult, CompareStatus, CompareVideoDetail } from '../../models/library.model';

interface ModeOption {
  value: CompareMode;
  icon: string;
  label: string;
}

@Component({
  selector: 'app-library-compare',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './library-compare.component.html',
  styleUrl: './library-compare.component.css',
})
export class LibraryCompareComponent {
  private readonly libraryService = inject(LibraryService);
  private readonly host = inject(ElementRef<HTMLElement>);

  readonly libraries = this.libraryService.libraries;

  readonly modes: ModeOption[] = [
    { value: 'identical', icon: '=', label: 'Identique' },
    { value: 'missing_right', icon: '>', label: 'Manquant à droite' },
    { value: 'missing_left', icon: '<', label: 'Manquant à gauche' },
  ];

  readonly leftId = signal<number | null>(null);
  readonly rightId = signal<number | null>(null);
  readonly mode = signal<CompareMode>('identical');
  readonly depth = signal<CompareDepth>('simple');
  readonly modeOpen = signal(false);
  /** Case « Voir les détails des différences uniquement » (mode Identique + approfondie). */
  readonly detailsOnly = signal(false);

  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly result = signal<CompareResult | null>(null);

  // readonly currentMode = computed(() => this.modes.find((m) => m.value === this.mode()) ?? this.modes[0]);
  readonly currentMode = computed<ModeOption>(() => {
    const mode = this.modes.find((m) => m.value === this.mode());
    return mode ?? this.modes[0]!;
  });

  /** La 3e option n'existe que pour « Identique » + « Comparaison approfondie ». */
  readonly detailsAvailable = computed(() => this.mode() === 'identical' && this.depth() === 'deep');
  readonly detailsActive = computed(() => this.detailsAvailable() && this.detailsOnly());

  /** Exécuter : bibliothèque #1 et #2 choisies, et différentes. */
  readonly canRun = computed(() => {
    const left = this.leftId();
    const right = this.rightId();
    return left !== null && right !== null && left !== right && !this.loading();
  });

  private readonly statusLabels: Record<CompareStatus, string> = {
    identical: 'identique',
    identical_different_file: 'vidéo différente',
    missing_right: 'manquant à droite',
    missing_left: 'manquant à gauche',
  };

  statusLabel(status: CompareStatus): string {
    return this.statusLabels[status];
  }

  // Un changement de paramètre invalide le tableau affiché : il ne correspondrait plus aux choix.
  setLeft(id: number | null): void { this.leftId.set(id); this.resetResult(); }
  setRight(id: number | null): void { this.rightId.set(id); this.resetResult(); }
  setDepth(depth: CompareDepth): void { this.depth.set(depth); this.resetResult(); }

  setDetailsOnly(checked: boolean): void {
    this.detailsOnly.set(checked);
    // Réactualise le tableau déjà affiché avec le nouveau filtre.
    if (this.result() !== null) this.execute();
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

  resolution(detail: CompareVideoDetail): string {
    return detail.width && detail.height ? `${detail.width}x${detail.height}` : '—';
  }

  chooseMode(option: ModeOption): void {
    this.mode.set(option.value);
    this.modeOpen.set(false);
    this.resetResult();
  }

  toggleModeList(): void {
    this.modeOpen.update((open) => !open);
  }

  /** Flèches haut/bas sur le sélecteur de mode (comme une liste native), Échap pour fermer. */
  onModeKeydown(event: KeyboardEvent): void {
    if (event.key === 'Escape') {
      this.modeOpen.set(false);
      return;
    }

    if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') return;

    event.preventDefault();

    const index = this.modes.findIndex((m) => m.value === this.mode());

    const next =
      event.key === 'ArrowDown'
        ? Math.min(index + 1, this.modes.length - 1)
        : Math.max(index - 1, 0);

    this.mode.set(this.modes[next]!.value);
    this.resetResult();
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (!this.modeOpen()) return;
    const dropdown = (this.host.nativeElement as HTMLElement).querySelector('.mode-select');
    if (dropdown && !dropdown.contains(event.target as Node)) {
      this.modeOpen.set(false);
    }
  }

  execute(): void {
    const left = this.leftId();
    const right = this.rightId();
    if (!this.canRun() || left === null || right === null) return;

    this.loading.set(true);
    this.error.set(null);
    this.result.set(null);

    this.libraryService.compareLibraries(left, right, this.mode(), this.depth(), this.detailsActive()).subscribe({
      next: (result) => {
        this.result.set(result);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? 'La comparaison a échoué. Vérifiez que le serveur est démarré.');
        this.loading.set(false);
      },
    });
  }

  private resetResult(): void {
    this.result.set(null);
    this.error.set(null);
  }
}
