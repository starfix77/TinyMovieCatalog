import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';

import { APP_LATEST_RELEASE_API_URL, APP_REPOSITORY_URL, APP_VERSION } from '../config/app-settings';

/** Champs utiles de la reponse de l'API GitHub « releases/latest ». */
interface GithubRelease {
  tag_name?: string;
  name?: string | null;
  body?: string | null;
  html_url?: string;
  published_at?: string | null;
}

export interface UpdateCheckResult {
  /** Version installee (sans prefixe « v »). */
  currentVersion: string;
  /** Derniere version publiee (sans prefixe « v »). */
  latestVersion: string;
  /** Vrai si la version publiee est differente de la version installee et plus recente. */
  updateAvailable: boolean;
  /** Release notes au format Markdown (propriete JSON « body »). */
  releaseNotes: string;
  releaseName: string;
  releaseUrl: string;
  publishedAt: string | null;
}

/** Retire un eventuel prefixe « v » / « V » et les espaces (« v0.9.37 » -> « 0.9.37 »). */
export function normalizeVersion(version: string): string {
  return version.trim().replace(/^v/i, '');
}

/** Compare deux versions numeriques « a.b.c » : <0 si a < b, 0 si egales, >0 si a > b. */
export function compareVersions(a: string, b: string): number {
  const pa = normalizeVersion(a).split(/[.-]/).map((n) => parseInt(n, 10) || 0);
  const pb = normalizeVersion(b).split(/[.-]/).map((n) => parseInt(n, 10) || 0);
  const len = Math.max(pa.length, pb.length);
  for (let i = 0; i < len; i++) {
    const d = (pa[i] ?? 0) - (pb[i] ?? 0);
    if (d !== 0) return d;
  }
  return 0;
}

/** Verification des mises a jour via l'API GitHub (appel direct depuis le navigateur). */
@Injectable({ providedIn: 'root' })
export class UpdateService {
  constructor(private http: HttpClient) {}

  checkForUpdate(): Observable<UpdateCheckResult> {
    return this.http
      .get<GithubRelease>(APP_LATEST_RELEASE_API_URL, {
        headers: { Accept: 'application/vnd.github+json' },
      })
      .pipe(
        map((release) => {
          const tag = release.tag_name?.trim();
          if (!tag) {
            throw new Error('Réponse GitHub invalide : propriété « tag_name » absente.');
          }
          const currentVersion = normalizeVersion(APP_VERSION);
          const latestVersion = normalizeVersion(tag);
          return {
            currentVersion,
            latestVersion,
            // Differente ET plus recente : une version locale en avance (developpement)
            // n'est pas signalee comme « mise a jour disponible ».
            updateAvailable:
              currentVersion !== latestVersion && compareVersions(latestVersion, currentVersion) > 0,
            releaseNotes: release.body ?? '',
            releaseName: release.name?.trim() || tag,
            releaseUrl: release.html_url || `${APP_REPOSITORY_URL}releases/latest`,
            publishedAt: release.published_at ?? null,
          };
        }),
      );
  }
}
