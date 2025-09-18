import { Injectable } from '@angular/core';

export interface SavedItinerary {
  id: string;
  name: string;
  createdAt: number;
  answers: Record<string, any>;
  markdown: string;
}

const STORAGE_KEY = 'vc_itineraries_v1';

@Injectable({ providedIn: 'root' })
export class SavedItinerariesService {
  list(): SavedItinerary[] {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? (JSON.parse(raw) as SavedItinerary[]) : [];
    } catch {
      return [];
    }
  }

  save(item: SavedItinerary) {
    const list = this.list();
    const idx = list.findIndex((x) => x.id === item.id);
    if (idx >= 0) list[idx] = item; else list.unshift(item);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
  }

  remove(id: string) {
    const list = this.list().filter((x) => x.id !== id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
  }

  get(id: string): SavedItinerary | undefined {
    return this.list().find((x) => x.id === id);
  }
}
