import { Component, computed, effect, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Movie, VideoFile } from '../../models/movie.model';
import { LibraryService } from '../../services/library.service';
import { MovieService } from '../../services/movie.service';

interface DuplicateGroup {
  key: string;
  title: string;
  year: number | null;
  movies: Movie[];
  files: { movie: Movie; file: VideoFile }[];
  posterUrl: string | null;
}

/** Groupe de doublons d'une serie TV : un meme episode present dans plusieurs fichiers. */
interface EpisodeDuplicateGroup {
  key: string;
  seriesTitle: string;
  /** Ex : "S01E01". */
  episodeLabel: string;
  files: { movie: Movie; file: VideoFile }[];
}

@Component({
  selector: 'app-duplicates',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './duplicates.component.html',
  styleUrl: './duplicates.component.css',
})
export class DuplicatesComponent {
  readonly libraryService = inject(LibraryService);
  private readonly movieService = inject(MovieService);
  readonly groups = signal<DuplicateGroup[]>([]);
  /** Doublons d'episodes (bibliotheques "Series TV"). */
  readonly episodeGroups = signal<EpisodeDuplicateGroup[]>([]);
  readonly isTv = computed(() => this.libraryService.activeLibrary()?.media_type === 'tv');
  readonly loading = signal(false);
  readonly error = signal('');
  readonly collapsed = signal<Set<string>>(new Set());
  private requestToken = 0;

  constructor() {
    effect(() => {
      const libraryId = this.libraryService.activeLibraryId();
      this.libraryService.moviesRefreshTick();
      const isTv = this.isTv();
      if (libraryId) this.load(libraryId, isTv);
      else { this.groups.set([]); this.episodeGroups.set([]); }
    });
  }

  private load(libraryId: number, isTv: boolean): void {
    const token = ++this.requestToken;
    this.loading.set(true);
    this.error.set('');
    this.movieService.listMovies(libraryId).subscribe({
      next: (page) => {
        if (token !== this.requestToken) return;
        if (isTv) {
          this.groups.set([]);
          this.episodeGroups.set(this.buildEpisodeGroups(page.items));
          this.loading.set(false);
          return;
        }
        this.episodeGroups.set([]);
        const map = new Map<string, { movies: Movie[]; files: { movie: Movie; file: VideoFile }[] }>();
        for (const movie of page.items) {
          const files = movie.video_files ?? [];
          if (!files.length) continue;
          const key = this.normalize(movie.title);
          const group = map.get(key) ?? { movies: [], files: [] };
          group.movies.push(movie);
          for (const file of files) group.files.push({ movie, file });
          map.set(key, group);
        }
        const groups: DuplicateGroup[] = [];
        for (const [key, group] of map) {
          if (group.files.length < 2) continue;
          const representative = group.movies[0];

          if (!representative) {
            continue;
          }
          
          groups.push({
            key,
            title: representative.title,
            year: representative.year,
            movies: group.movies,
            files: group.files,
            posterUrl: this.movieService.posterUrl(representative),
          });
        }
        this.groups.set(groups.sort((a, b) => a.title.localeCompare(b.title, 'fr')));
        this.loading.set(false);
      },
      error: () => {
        if (token !== this.requestToken) return;
        this.error.set('Impossible de charger les fichiers de la bibliothèque.');
        this.loading.set(false);
      },
    });
  }

  // ---------- Series TV : detection des episodes en double ----------
  private static readonly RE_SXXEXX = /s(\d{1,2})[\s._-]?e(\d{1,3})(?!\d)/i;               // S01E02
  private static readonly RE_NXNN = /(?<!\d)(\d{1,2})x(\d{2,3})(?!\d)/i;                    // 1x02
  private static readonly RE_EPONLY = /(?:^|[\s._-])e(?:p(?:isode)?)?[\s._-]?(\d{1,3})(?!\d)/i; // E02, Ep02, Episode 02
  private static readonly RE_SEASON_DIR = /(?:saison|season)[\s._-]*(\d{1,2})(?!\d)|(?:^|[\\/\s._-])s(\d{1,2})(?=$|[\\/\s._-])/i;

  /** Saison / episode d'un fichier. La saison absente du nom de fichier est
   *  deduite du dossier ("Saison 1", "Season 01", "S01"), sinon saison 1. */
  private parseEpisode(file: VideoFile): { season: number; episode: number } | null {
    const name = file.filename || (file.filepath || '').split(/[\\/]/).pop() || '';
    let m = DuplicatesComponent.RE_SXXEXX.exec(name) ?? DuplicatesComponent.RE_NXNN.exec(name);
    if (m) return { season: Number(m[1]), episode: Number(m[2]) };
    m = DuplicatesComponent.RE_EPONLY.exec(name);
    if (!m) return null;
    const episode = Number(m[1]);
    // Dossiers du plus proche au plus lointain (le nom de fichier est exclu).
    const dirs = (file.filepath || '').split(/[\\/]/).slice(0, -1).reverse();
    for (const dir of dirs) {
      const d = DuplicatesComponent.RE_SEASON_DIR.exec(dir);
      if (d) return { season: Number(d[1] ?? d[2]), episode };
    }
    return { season: 1, episode };
  }

  private buildEpisodeGroups(series: Movie[]): EpisodeDuplicateGroup[] {
    const map = new Map<string, EpisodeDuplicateGroup & { season: number; episode: number }>();
    for (const movie of series) {
      for (const file of movie.video_files ?? []) {
        const ep = this.parseEpisode(file);
        if (!ep) continue;
        const key = `${this.normalize(movie.title)}|${ep.season}|${ep.episode}`;
        let group = map.get(key);
        if (!group) {
          const label = `S${String(ep.season).padStart(2, '0')}E${String(ep.episode).padStart(2, '0')}`;
          group = { key, seriesTitle: movie.title, episodeLabel: label, season: ep.season, episode: ep.episode, files: [] };
          map.set(key, group);
        }
        group.files.push({ movie, file });
      }
    }
    return [...map.values()]
      .filter(g => g.files.length >= 2)
      .sort((a, b) => a.seriesTitle.localeCompare(b.seriesTitle, 'fr') || a.season - b.season || a.episode - b.episode)
      .map(({ season, episode, ...group }) => ({
        ...group,
        files: group.files.sort((x, y) => (x.file.filepath || '').localeCompare(y.file.filepath || '', 'fr')),
      }));
  }

  private normalize(value: string): string {
    return (value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('fr').trim();
  }

  toggle(key: string): void {
    this.collapsed.update((current) => {
      const next = new Set(current);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  isCollapsed(key: string): boolean { return this.collapsed().has(key); }

  private currentKeys(): string[] {
    return this.isTv() ? this.episodeGroups().map(g => g.key) : this.groups().map(g => g.key);
  }

  /** Nombre de sections affichees (films : titres ; series : episodes). */
  readonly sectionCount = computed(() => this.isTv() ? this.episodeGroups().length : this.groups().length);

  /** Vrai quand toutes les sections sont reduites. */
  readonly allCollapsed = computed(() => {
    const keys = this.currentKeys();
    const collapsed = this.collapsed();
    return keys.length > 0 && keys.every(k => collapsed.has(k));
  });

  /** Reduit toutes les sections, ou les developpe toutes si elles sont deja reduites. */
  toggleAll(): void {
    if (this.allCollapsed()) this.collapsed.set(new Set());
    else this.collapsed.set(new Set(this.currentKeys()));
  }

  formatSize(bytes: number): string {
    if (!bytes) return '—';
    if (bytes >= 1024 ** 3) return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
    if (bytes >= 1024 ** 2) return `${(bytes / 1024 ** 2).toFixed(0)} MB`;
    return `${(bytes / 1024).toFixed(0)} KB`;
  }

  formatBitrate(bitsPerSec: number | null): string {
    return bitsPerSec ? `${Math.round(bitsPerSec / 1000)} kb/s` : '—';
  }

  trackEpisodeGroup(_: number, group: EpisodeDuplicateGroup): string { return group.key; }
  trackGroup(_: number, group: DuplicateGroup): string { return group.key; }
  trackFile(_: number, item: { movie: Movie; file: VideoFile }): number { return item.file.id; }
}
