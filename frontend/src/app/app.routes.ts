import { Routes } from '@angular/router';
import { MovieGridComponent } from './components/movie-grid/movie-grid.component';
import { MovieTableComponent } from './components/movie-table/movie-table.component';
import { GenreViewComponent } from './components/genre-view/genre-view.component';
import { SagaViewComponent } from './components/saga-view/saga-view.component';
import { ActorViewComponent } from './components/actor-view/actor-view.component';
import { LibraryInfoComponent } from './components/library-info/library-info.component';
import { LibraryCompareComponent } from './components/library-compare/library-compare.component';
import { LibraryToolsComponent } from './components/library-tools/library-tools.component';
import { LibraryExportComponent } from './components/library-export/library-export.component';
import { LibraryImportComponent } from './components/library-import/library-import.component';
import { DuplicatesComponent } from './components/duplicates/duplicates.component';

export const routes: Routes = [
  { path: '', component: MovieGridComponent, title: 'TinyMovieCatalog — Vignettes' },
  { path: 'genres', component: GenreViewComponent, title: 'TinyMovieCatalog — Genre' },
  { path: 'sagas', component: SagaViewComponent, title: 'TinyMovieCatalog — Sagas' },
  { path: 'acteurs', component: ActorViewComponent, title: 'TinyMovieCatalog — Acteur / Filmographie' },
  { path: 'technique', component: MovieTableComponent, title: 'TinyMovieCatalog — Detail technique' },
  { path: 'doublons', component: DuplicatesComponent, title: 'TinyMovieCatalog — Doublons' },
  { path: 'info', component: LibraryInfoComponent, title: 'TinyMovieCatalog — Info' },
  { path: 'outils', component: LibraryToolsComponent, title: 'TinyMovieCatalog — Outils des bibliothèques' },
  { path: 'outils/comparaison', component: LibraryCompareComponent, title: 'TinyMovieCatalog — Comparaison' },
  { path: 'outils/export', component: LibraryExportComponent, title: 'TinyMovieCatalog — Exporter une bibliothèque' },
  { path: 'outils/import', component: LibraryImportComponent, title: 'TinyMovieCatalog — Importer une bibliothèque' },
  { path: 'comparaison', redirectTo: 'outils/comparaison', pathMatch: 'full' },  // ancienne URL
  { path: '**', redirectTo: '' },
];
