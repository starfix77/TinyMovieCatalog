import { Routes } from '@angular/router';
import { MovieGridComponent } from './components/movie-grid/movie-grid.component';
import { MovieTableComponent } from './components/movie-table/movie-table.component';
import { GenreViewComponent } from './components/genre-view/genre-view.component';
import { SagaViewComponent } from './components/saga-view/saga-view.component';
import { ActorViewComponent } from './components/actor-view/actor-view.component';
import { LibraryInfoComponent } from './components/library-info/library-info.component';

export const routes: Routes = [
  { path: '', component: MovieGridComponent, title: 'TinyMovieCatalog — Vignettes' },
  { path: 'genres', component: GenreViewComponent, title: 'TinyMovieCatalog — Genre' },
  { path: 'sagas', component: SagaViewComponent, title: 'TinyMovieCatalog — Sagas' },
  { path: 'acteurs', component: ActorViewComponent, title: 'TinyMovieCatalog — Acteur / Filmographie' },
  { path: 'technique', component: MovieTableComponent, title: 'TinyMovieCatalog — Detail technique' },
  { path: 'info', component: LibraryInfoComponent, title: 'TinyMovieCatalog — Info' },
  { path: '**', redirectTo: '' },
];
