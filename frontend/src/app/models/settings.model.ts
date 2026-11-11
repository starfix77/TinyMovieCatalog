/** Origine de la valeur d'un parametre. */
export type SettingSource = 'env_file' | 'environment' | 'default';

/** Un parametre du fichier backend/.env (les secrets sont masques par le backend). */
export interface SettingItem {
  name: string;
  value: string;
  description: string;
  source: SettingSource;
  /** false = cle presente dans le .env mais non reconnue (ignoree par l'application). */
  known: boolean;
  secret: boolean;
}

export interface AppSettings {
  env_file: string;
  env_file_exists: boolean;
  items: SettingItem[];
}
