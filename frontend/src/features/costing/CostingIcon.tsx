export default function CostingIcon({ name }: { name: string }) {
  const paths: Record<string, string> = {
    summary: "M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z",
    recipes: "M12 5v16 M12 5C9 2 5 3 2 4v15c4-1 7-1 10 2 3-3 6-3 10-2V4c-3-1-7-2-10 1Z",
    ingredients: "M4 8h16l-2 13H6L4 8Z M8 8l4-6 4 6 M9 12v5 M15 12v5",
    inventory: "M3 7l9-5 9 5v10l-9 5-9-5V7Z M3 7l9 5 9-5 M12 12v10 M7 4l10 6",
  };
  return <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name] ?? paths.recipes} /></svg>;
}
