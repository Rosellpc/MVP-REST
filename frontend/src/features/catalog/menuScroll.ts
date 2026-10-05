const positions = new Map<string, number>();
export function rememberMenuPosition(category: string) {
  positions.set(category, window.scrollY);
}
export function menuPosition(category: string) {
  return positions.get(category) ?? 0;
}
