import { Routes } from '@angular/router';
import { MovieGridComponent } from './components/movie-grid/movie-grid.component';
import { MovieTableComponent } from './components/movie-table/movie-table.component';

export const routes: Routes = [
  { path: '', component: MovieGridComponent, title: 'TinyMovieCatalog — Vignettes' },
  { path: 'technique', component: MovieTableComponent, title: 'TinyMovieCatalog — Detail technique' },
  { path: '**', redirectTo: '' },
];
