export function ymKey(y: number, m: number): string {
  return `${String(y).padStart(4, "0")}-${String(m).padStart(2, "0")}`;
}

export function parseYm(s: string): { y: number; m: number } {
  const [y, m] = s.split("-").map(Number);
  return { y: y ?? 0, m: m ?? 0 };
}

export function monthRange(first: string, last: string): string[] {
  const a = parseYm(first);
  const b = parseYm(last);
  const out: string[] = [];
  let { y, m } = a;
  while (y * 100 + m <= b.y * 100 + b.m) {
    out.push(ymKey(y, m));
    m += 1;
    if (m > 12) {
      m = 1;
      y += 1;
    }
  }
  return out;
}

export function daysInMonth(ym: string): number {
  const { y, m } = parseYm(ym);
  return new Date(Date.UTC(y, m, 0)).getUTCDate();
}

const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const MONTH_LONG = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

export function monthShort(m: number): string {
  return MONTH_NAMES[m - 1] ?? "";
}

export function monthLong(m: number): string {
  return MONTH_LONG[m - 1] ?? "";
}

export function ymLabel(ym: string): string {
  const { y, m } = parseYm(ym);
  return `${monthLong(m)} ${y}`;
}
