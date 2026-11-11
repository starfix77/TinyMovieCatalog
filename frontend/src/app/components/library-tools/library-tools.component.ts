import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import { AppDialogService } from '../../services/app-dialog.service';

/**
 * Vue « Outil des bibliothèques » : point d'entrée du bouton « Outils » du
 * bandeau de gauche. Gros boutons (icône + texte) :
 * - comparer, exporter, importer (outils des bibliothèques) ;
 * - section « Application » : « À propos » et « Paramètres » (boîtes de dialogue).
 */
@Component({
  selector: 'app-library-tools',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './library-tools.component.html',
  styleUrls: ['./tools-shared.css', './library-tools.component.css'],
})
export class LibraryToolsComponent {
  protected readonly dialogs = inject(AppDialogService);
}
