import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

/**
 * Vue « Outil des bibliothèques » : point d'entrée du bouton « Outils » du
 * bandeau de gauche. Trois gros boutons (icône + texte) :
 * comparer, exporter, importer.
 */
@Component({
  selector: 'app-library-tools',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './library-tools.component.html',
  styleUrls: ['./tools-shared.css', './library-tools.component.css'],
})
export class LibraryToolsComponent {}
