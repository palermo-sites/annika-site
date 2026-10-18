export const base = import.meta.env.BASE_URL.replace(/\/$/, '');
export const url = (p: string) => `${base}${p.startsWith('/') ? p : `/${p}`}`;
export const img = (name: string) => url(`/images/${name}`);
export const vid = (name: string) => url(`/videos/${name}`);
