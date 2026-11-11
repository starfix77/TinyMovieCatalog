/**
 * Parametres generaux de l'application cote frontend.
 *
 * Fichier unique, importable par tous les composants :
 *   import { APP_VERSION } from '../../config/app-settings';
 *
 * A CHAQUE NOUVELLE VERSION : modifier uniquement APP_VERSION ci-dessous
 * (le script update_tinymoviecatalog.sh lit la version dans ce fichier).
 */

/** Nom de l'application. */
export const APP_NAME = 'TinyMovieCatalog';

/** Version de l'application (affichee dans la fenetre « A propos » et l'info-bulle du titre). */
export const APP_VERSION = '0.9.37';

/** Depot du code source et de la documentation. */
export const APP_REPOSITORY_URL = 'https://github.com/starfix77/TinyMovieCatalog/';

/** API GitHub : derniere release publiee (propriete JSON « tag_name » = version, « body » = release notes). */
export const APP_LATEST_RELEASE_API_URL =
  'https://api.github.com/repos/starfix77/TinyMovieCatalog/releases/latest';
