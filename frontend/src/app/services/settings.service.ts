import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { AppSettings } from '../models/settings.model';

@Injectable({ providedIn: 'root' })
export class SettingsService {
  private readonly baseUrl = `${environment.apiUrl}/settings`;

  constructor(private http: HttpClient) {}

  /** Parametres du fichier backend/.env (lecture seule). */
  getSettings(): Observable<AppSettings> {
    return this.http.get<AppSettings>(this.baseUrl);
  }
}
