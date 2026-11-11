/**
 * Convertisseur Markdown -> HTML minimaliste (sans dependance) destine a l'affichage
 * des release notes GitHub dans la fenetre « A propos ».
 *
 * Supporte : titres (#), gras, italique, barre, code en ligne, blocs de code (```),
 * listes a puces / numerotees (avec imbrication et cases a cocher), citations (>),
 * separateurs (---), tableaux, liens [texte](url) et URL nues.
 *
 * Securite : tout le texte source est echappe en HTML AVANT la mise en forme ; seuls les
 * liens http(s) sont conserves. Le resultat est de plus filtre par le sanitizer d'Angular
 * lorsqu'il est affiche via [innerHTML].
 */

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

const PH = '\u0000';

/** Mise en forme « en ligne » d'un texte DEJA echappe. */
function inline(escaped: string): string {
  const store: string[] = [];
  const keep = (html: string): string => {
    store.push(html);
    return `${PH}${store.length - 1}${PH}`;
  };

  // Le caractere NUL sert de marqueur interne : on le retire du texte source.
  // eslint-disable-next-line no-control-regex
  let t = escaped.replace(/\u0000/g, '');

  // Code en ligne.
  t = t.replace(/`([^`\n]+)`/g, (_m, code: string) => keep(`<code>${code}</code>`));

  // Images ![alt](url) : remplacees par un lien vers l'image (pas de chargement distant).
  t = t.replace(/!\[([^\]]*)\]\((https?:\/\/[^\s)]+)\)/g, (_m, alt: string, url: string) =>
    keep(`<a href="${url}" target="_blank" rel="noopener noreferrer">${alt || url}</a>`),
  );

  // Liens [texte](url) (http/https uniquement).
  t = t.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, (_m, label: string, url: string) =>
    keep(`<a href="${url}" target="_blank" rel="noopener noreferrer">${label}</a>`),
  );

  // URL nues.
  t = t.replace(/(^|[\s(])(https?:\/\/[^\s<)]+[^\s<).,;:!?])/g, (_m, pre: string, url: string) =>
    `${pre}${keep(`<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`)}`,
  );

  // Gras, italique, barre.
  t = t.replace(/\*\*([^*\n]+?)\*\*/g, '<strong>$1</strong>');
  t = t.replace(/(^|[^\w])__([^_\n]+?)__(?!\w)/g, '$1<strong>$2</strong>');
  t = t.replace(/\*([^*\s][^*\n]*?)\*/g, '<em>$1</em>');
  t = t.replace(/(^|[^\w])_([^_\s][^_\n]*?)_(?!\w)/g, '$1<em>$2</em>');
  t = t.replace(/~~([^~\n]+?)~~/g, '<del>$1</del>');

  // Restitution des fragments proteges.
  // eslint-disable-next-line no-control-regex
  return t.replace(/\u0000(\d+)\u0000/g, (_m, i: string) => store[Number(i)] ?? '');
}

function splitTableRow(line: string): string[] {
  let l = line.trim();
  if (l.startsWith('|')) l = l.slice(1);
  if (l.endsWith('|')) l = l.slice(0, -1);
  return l.split('|').map((c) => c.trim());
}

const RE_FENCE = /^\s*```/;
const RE_HEADING = /^(#{1,6})\s+(.*?)\s*#*\s*$/;
const RE_HR = /^\s*([-*_])(\s*\1){2,}\s*$/;
const RE_LIST = /^(\s*)([-*+]|\d+[.)])\s+(.*)$/;
const RE_QUOTE = /^\s*>\s?(.*)$/;
const RE_TABLE_SEP = /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$/;

/** Convertit du Markdown en HTML (fragment). Retourne '' si le texte est vide. */
export function markdownToHtml(markdown: string | null | undefined): string {
  if (!markdown) return '';
  const lines = markdown.replace(/\r\n?/g, '\n').split('\n');
  const out: string[] = [];
  let i = 0;
  const L = (n: number): string => lines[n] ?? '';

  while (i < lines.length) {
    const line = L(i);

    // Ligne vide.
    if (line.trim() === '') {
      i++;
      continue;
    }

    // Bloc de code.
    if (RE_FENCE.test(line)) {
      const code: string[] = [];
      i++;
      while (i < lines.length && !RE_FENCE.test(L(i))) {
        code.push(L(i));
        i++;
      }
      i++; // fence fermante
      out.push(`<pre><code>${escapeHtml(code.join('\n'))}</code></pre>`);
      continue;
    }

    // Titre.
    const h = RE_HEADING.exec(line);
    if (h) {
      const level = (h[1] ?? '#').length;
      out.push(`<h${level}>${inline(escapeHtml(h[2] ?? ''))}</h${level}>`);
      i++;
      continue;
    }

    // Separateur.
    if (RE_HR.test(line)) {
      out.push('<hr />');
      i++;
      continue;
    }

    // Citation.
    if (RE_QUOTE.test(line)) {
      const quote: string[] = [];
      while (i < lines.length && RE_QUOTE.test(L(i))) {
        quote.push(RE_QUOTE.exec(L(i))?.[1] ?? '');
        i++;
      }
      out.push(`<blockquote>${markdownToHtml(quote.join('\n'))}</blockquote>`);
      continue;
    }

    // Tableau.
    if (line.includes('|') && i + 1 < lines.length && RE_TABLE_SEP.test(L(i + 1))) {
      const head = splitTableRow(line);
      i += 2;
      const rows: string[][] = [];
      while (i < lines.length && L(i).trim() !== '' && L(i).includes('|')) {
        rows.push(splitTableRow(L(i)));
        i++;
      }
      const th = head.map((c) => `<th>${inline(escapeHtml(c))}</th>`).join('');
      const tr = rows
        .map((r) => `<tr>${r.map((c) => `<td>${inline(escapeHtml(c))}</td>`).join('')}</tr>`)
        .join('');
      out.push(`<table><thead><tr>${th}</tr></thead><tbody>${tr}</tbody></table>`);
      continue;
    }

    // Liste (imbriquee).
    if (RE_LIST.test(line)) {
      const stack: { indent: number; tag: 'ul' | 'ol' }[] = [];
      const top = (): { indent: number; tag: 'ul' | 'ol' } | undefined => stack[stack.length - 1];
      let html = '';
      while (i < lines.length) {
        const m = RE_LIST.exec(L(i));
        if (!m) {
          // Ligne de continuation indentee d'un element de liste.
          if (L(i).trim() !== '' && /^\s{2,}\S/.test(L(i)) && stack.length) {
            html = html.replace(/<\/li>$/, ` ${inline(escapeHtml(L(i).trim()))}</li>`);
            i++;
            continue;
          }
          break;
        }
        const indent = (m[1] ?? '').replace(/\t/g, '    ').length;
        const tag: 'ul' | 'ol' = /\d/.test(m[2] ?? '') ? 'ol' : 'ul';
        let content = m[3] ?? '';

        // Fermeture des niveaux plus profonds.
        while (stack.length && indent < (top()?.indent ?? 0)) {
          html += `</li></${stack.pop()!.tag}>`;
        }
        if (!stack.length || indent > (top()?.indent ?? 0)) {
          html += `<${tag}>`;
          stack.push({ indent, tag });
        } else {
          html += '</li>';
        }

        let task = '';
        const tm = /^\[([ xX])\]\s+(.*)$/.exec(content);
        if (tm) {
          task = tm[1] === ' ' ? '☐ ' : '☑ ';
          content = tm[2] ?? '';
        }
        html += `<li>${task}${inline(escapeHtml(content))}`;
        i++;
      }
      while (stack.length) {
        html += `</li></${stack.pop()!.tag}>`;
      }
      out.push(html);
      continue;
    }

    // Paragraphe : lignes consecutives jusqu'au prochain bloc.
    const para: string[] = [];
    while (
      i < lines.length &&
      L(i).trim() !== '' &&
      !RE_FENCE.test(L(i)) &&
      !RE_HEADING.test(L(i)) &&
      !RE_HR.test(L(i)) &&
      !RE_QUOTE.test(L(i)) &&
      !RE_LIST.test(L(i))
    ) {
      para.push(L(i).trim());
      i++;
    }
    out.push(`<p>${para.map((l) => inline(escapeHtml(l))).join('<br />')}</p>`);
  }

  return out.join('\n');
}
