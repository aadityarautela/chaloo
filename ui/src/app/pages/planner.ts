import { Component, computed, inject, signal, OnInit, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { QuestionsService, Question } from '../services/questions.service';
import { ItineraryService } from '../services/itinerary.service';
import { SavedItinerariesService, SavedItinerary } from '../services/saved.service';
import { MarkdownModule } from 'ngx-markdown';
import { debounceTime } from 'rxjs';

@Component({
  selector: 'app-planner-page',
  standalone: true,
  imports: [CommonModule, FormsModule, MarkdownModule],
  template: `
    <main class="min-h-[calc(100vh-64px)] ">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div class="mb-8">
          <h1 class="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-800">Smart Trip Planner</h1>
          <p class="mt-2 text-slate-600">Answer one question at a time on the left. Your itinerary updates on the right.</p>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Left: Questions (stepper) -->
          <section class="relative border border-slate-200/70 dark:border-slate-700 rounded-2xl p-5 shadow-sm">
            <div class="flex items-center justify-between mb-3">
              <h2 class="text-xl font-semibold text-slate-800">Questions</h2>
              <button type="button" (click)="reset()" class="text-sm text-slate-600 hover:text-slate-900 underline">Reset</button>
            </div>

            <ng-container *ngIf="questions().length; else loading">
              <div class="mb-4">
                <div class="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div class="h-full bg-green-500 transition-all" [style.width.%]="progressPct()"></div>
                </div>
                <div class="mt-2 text-xs text-slate-600">Step {{ stepIndex()+1 }} of {{ questions().length }}</div>
              </div>

              <div class="rounded-xl border border-slate-200 dark:border-slate-700 p-4">
                <ng-container *ngIf="currentQuestion() as q">
                  <div class="flex items-start justify-between gap-3">
                    <div>
                      <h3 class="text-base font-medium text-slate-800">{{ q.title }}</h3>
                      <p class="text-sm text-slate-500" *ngIf="q.description">{{ q.description }}</p>
                    </div>
                    <span class="text-xs text-slate-500">{{ q.required ? 'Required' : 'Optional' }}</span>
                  </div>

                  <div class="mt-4">
                    <!-- single-select -->
                    <div *ngIf="q.type === 'single-select'" class="flex flex-wrap gap-2">
                      <button *ngFor="let opt of q.options" type="button" (click)="selectSingle(q.id, opt.value); autoNext()" [class]="chipClass(isSelectedSingle(q.id, opt.value))">{{ opt.label }}</button>
                    </div>

                    <!-- multi-select -->
                    <div *ngIf="q.type === 'multi-select'" class="flex flex-wrap gap-2">
                      <button *ngFor="let opt of q.options" type="button" (click)="toggleMulti(q.id, opt.value)" [class]="chipClass(isSelectedMulti(q.id, opt.value))">{{ opt.label }}</button>
                    </div>

                    <!-- text -->
                    <div *ngIf="q.type === 'text'">
                      <input type="text" class="w-full rounded-lg border border-slate-300 focus:ring-2 focus:ring-green-400 focus:border-green-400 px-3 py-2 bg-white/90" [placeholder]="q.placeholder || ''" [ngModel]="getText(q.id)" (ngModelChange)="setText(q.id, $event)" (keyup.enter)="next()" />
                    </div>

                    <!-- number -->
                    <div *ngIf="q.type === 'number'" class="grid grid-cols-7 items-center gap-3">
                      <input type="range" class="col-span-6 accent-green-500" [min]="q.min ?? 1" [max]="q.max ?? 10" [step]="q.step ?? 1" [ngModel]="getNumber(q.id)" (ngModelChange)="setNumber(q.id, toNumber($event))" />
                      <div class="col-span-1">
                        <input type="number" class="w-full rounded border border-slate-300 px-2 py-1" [min]="q.min ?? 1" [max]="q.max ?? 10" [step]="q.step ?? 1" [ngModel]="getNumber(q.id)" (ngModelChange)="setNumber(q.id, toNumber($event))" />
                      </div>
                    </div>

                    <!-- date -->
                    <div *ngIf="q.type === 'date'">
                      <input type="date" class="rounded-lg border border-slate-300 px-3 py-2" [ngModel]="getText(q.id)" (ngModelChange)="setText(q.id, $event)" />
                    </div>
                  </div>

                  <div class="mt-6 flex items-center justify-between">
                    <div class="flex gap-2">
                      <button type="button" (click)="prev()" [disabled]="stepIndex() === 0" class="px-3 py-2 rounded-lg border border-slate-300 disabled:opacity-50">Back</button>
                    </div>
                    <div class="flex gap-2" *ngIf="!q.required">
                      <button type="button" (click)="prev()" class="px-3 py-2 rounded-lg border border-slate-300 disabled:opacity-50">Skip</button>
                    </div>

                    <div class="flex gap-2">
                      <button type="button" (click)="next()" [disabled]="!canProceed(q)" class="px-4 py-2 rounded-lg bg-green-600 text-white hover:bg-green-700">Next</button>
                    </div>
                  </div>
                </ng-container>
              </div>

              <div class="mt-3 flex flex-wrap gap-2">
                <button *ngFor="let q of questions(); index as i" type="button" (click)="jumpTo(i)" [class]="stepPillClass(i)">{{ i + 1 }}</button>
              </div>


              <div class="mt-8 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
                <h3 class="text-sm font-medium text-slate-800 mb-2">Additional Comments</h3>
                <textarea class="w-full rounded-lg border border-slate-300 focus:ring-2 focus:ring-green-400 focus:border-green-400 px-3 py-2 bg-white/90" rows="4" placeholder="Any extra details or preferences?" [ngModel]="getText('additionalComments')" (ngModelChange)="setText('additionalComments', $event)"></textarea>
              </div>
            </ng-container>



            <ng-template #loading>
              <div class="animate-pulse space-y-4">
                <div class="h-6 bg-slate-200 rounded"></div>
                <div class="h-20 bg-slate-200 rounded"></div>
                <div class="h-16 bg-slate-200 rounded"></div>
              </div>
            </ng-template>
          </section>

          <!-- Right: Itinerary -->
          <section class="relative backdrop-blur border border-slate-200/70 dark:border-slate-700 rounded-2xl p-5 shadow-sm">
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-xl font-semibold text-slate-800">Your Itinerary</h2>
              <div class="flex items-center gap-3">
                <button type="button" (click)="saveCurrent()" class="text-sm text-green-700 hover:text-green-900 px-3 py-1.5 rounded-lg border border-green-200 bg-green-50">Save</button>
                <button type="button" (click)="toggleSaved()" class="text-sm text-slate-600 hover:text-slate-900">Saved</button>
                <button type="button" (click)="print()" class="text-sm text-green-600 hover:text-green-800">Print</button>
              </div>
            </div>

            <div *ngIf="showSaved()" class="absolute right-4 top-14 w-80 max-h-96 overflow-auto bg-white border border-slate-200 rounded-xl shadow-soft p-3 z-10">
              <div class="flex items-center justify-between mb-2">
                <h4 class="font-medium text-slate-800">Saved itineraries</h4>
                <button class="text-sm text-slate-500" (click)="toggleSaved()">Close</button>
              </div>
              <div *ngIf="savedList().length; else emptySaved" class="space-y-2">
                <div *ngFor="let it of savedList()" class="p-2 rounded-lg border border-slate-200 hover:bg-slate-50">
                  <div class="flex items-center justify-between">
                    <div>
                      <div class="text-sm font-medium text-slate-800">{{ it.name }}</div>
                      <div class="text-xs text-slate-500">{{ it.createdAt | date:'medium' }}</div>
                    </div>
                    <div class="flex items-center gap-2">
                      <button class="text-xs text-green-600" (click)="loadSaved(it)">Load</button>
                      <button class="text-xs text-rose-600" (click)="deleteSaved(it)">Delete</button>
                    </div>
                  </div>
                </div>
              </div>
              <ng-template #emptySaved>
                <div class="text-sm text-slate-500">No saved itineraries yet.</div>
              </ng-template>
            </div>

            <div *ngIf="itineraryMarkdown(); else empty" class="prose prose-slate max-w-none">
              <markdown [data]="itineraryMarkdown()"></markdown>
            </div>

            <ng-template #empty>
              <div class="text-center text-slate-500 p-10">
                <p class="mb-2">Begin the questionnaire to build your itinerary.</p>
                <p class="text-sm">Tip: set destination and trip days.</p>
              </div>
            </ng-template>
          </section>
        </div>
      </div>
    </main>
  `
})
export class PlannerPageComponent {
  private readonly questionsSvc = inject(QuestionsService);
  private readonly itinerarySvc = inject(ItineraryService);
  private readonly savedSvc = inject(SavedItinerariesService);

  readonly questions = signal<Question[]>([]);
  readonly answers = signal<Record<string, any>>({});
  readonly stepIndex = signal(0);
  readonly showSaved = signal(false);
  readonly itineraryMarkdown = signal<string>('');

  constructor() {
    this.questionsSvc.fetchQuestions().subscribe((qs) => this.questions.set(qs));
    
    // Set up effect to watch answers changes
    effect(() => {
      const answers = this.answers();
      if (Object.keys(answers).length > 0) {
        this.itinerarySvc.generateViaApi(answers).pipe(debounceTime(2000)).subscribe(
          markdownResponse => this.itineraryMarkdown.set(markdownResponse.result.response)
        );
      }
    });
  }

  readonly currentQuestion = computed(() => this.questions()[this.stepIndex()] as Question | undefined);
  readonly savedList = signal<SavedItinerary[]>(this.savedSvc.list());

  chipClass(active: boolean) {
    return (
      'px-3 py-1.5 rounded-full border text-sm transition ' +
      (active
        ? 'bg-green-600 text-white border-green-600 shadow-sm'
        : 'bg-white text-slate-700 border-slate-300 hover:border-slate-400 hover:bg-slate-50')
    );
  }
  stepPillClass(i: number) {
    const completed = this.isAnswered(this.questions()[i]?.id);
    const active = i === this.stepIndex();
    return (
      'h-8 w-8 flex items-center justify-center rounded-full text-sm ' +
      (active ? 'bg-green-600 text-white' : completed ? 'bg-green-100 text-sky-700' : 'bg-slate-100 text-slate-500')
    );
  }

  canProceed(q: Question | undefined) {
    if (!q) return false;
    if (!q.required) return true;
    return this.isAnswered(q.id);
  }

  isAnswered(id?: string) {
    if (!id) return false;
    const v = this.answers()[id];
    if (Array.isArray(v)) return v.length > 0;
    return v !== undefined && v !== null && String(v).toString().trim() !== '';
  }

  next() {
    const idx = this.stepIndex();
    if (idx < this.questions().length - 1) {
      this.stepIndex.set(idx + 1);
    }
  }
  prev() {
    const idx = this.stepIndex();
    if (idx > 0) this.stepIndex.set(idx - 1);
  }
  jumpTo(i: number) {
    if (i <= this.stepIndex()) this.stepIndex.set(i);
  }
  autoNext() {
    const q = this.currentQuestion();
    if (!q) return;
    if (q.type === 'single-select' && this.canProceed(q)) this.next();
  }

  selectSingle(id: string, value: string) {
    const next = { ...this.answers() };
    next[id] = value;
    this.answers.set(next);
  }

  isSelectedSingle(id: string, value: string) { return this.answers()[id] === value; }

  toggleMulti(id: string, value: string) {
    const curr: string[] = Array.isArray(this.answers()[id]) ? [...this.answers()[id]] : [];
    const idx = curr.indexOf(value);
    if (idx >= 0) curr.splice(idx, 1);
    else curr.push(value);
    const next = { ...this.answers() };
    next[id] = curr;
    this.answers.set(next);
  }

  isSelectedMulti(id: string, value: string) {
    const curr: string[] = this.answers()[id] || [];
    return Array.isArray(curr) && curr.includes(value);
  }

  getText(id: string) { return this.answers()[id] ?? ''; }
  setText(id: string, v: string) { const next = { ...this.answers() }; next[id] = v; this.answers.set(next); }

  getNumber(id: string) { return this.answers()[id] ?? 3; }
  setNumber(id: string, v: number) { const next = { ...this.answers() }; next[id] = v; this.answers.set(next); }

  toNumber(v: any) { const n = Number(v); return isNaN(n) ? 0 : n; }

  reset() {
    this.answers.set({});
    this.stepIndex.set(0);
  }

  progressPct() {
    const total = this.questions().length || 1;
    const idx = this.stepIndex();
    return Math.round(((idx) / total) * 100);
  }

  displayCity() {
    const c = (this.answers()['destination_city'] as string) || 'Your Trip';
    return c.trim().length ? c : 'Your Trip';
  }

  print() { window.print(); }

  saveCurrent() {
    const name = `${this.displayCity()} — ${new Date().toLocaleDateString()}`;
    const id = Math.random().toString(36).slice(2, 9);
    const answers = this.answers();
    this.itinerarySvc.generateViaApi(answers).subscribe(markdown => {
      const item: SavedItinerary = {
        id,
        name,
        createdAt: Date.now(),
        answers: answers,
        markdown: markdown,
      };
      this.savedSvc.save(item);
      this.savedList.set(this.savedSvc.list());
      this.showSaved.set(true);
    });
  }
  toggleSaved() { this.showSaved.set(!this.showSaved()); }
  loadSaved(it: SavedItinerary) {
    this.answers.set({ ...it.answers });
    this.itineraryMarkdown.set(it.markdown);
    this.stepIndex.set(this.questions().length - 1);
    this.showSaved.set(false);
  }
  deleteSaved(it: SavedItinerary) {
    this.savedSvc.remove(it.id);
    this.savedList.set(this.savedSvc.list());
  }
}
