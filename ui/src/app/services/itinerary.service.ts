import { HttpClient } from '@angular/common/http';
import { Question, QuestionsService } from './questions.service';
import { Injectable } from '@angular/core';
import { Observable, shareReplay, switchMap } from 'rxjs';

export interface PromptRequest {
  data: {
    answers: any;
    prompt: string;
    history: any[];
  }
}

@Injectable({ providedIn: 'root' })
export class ItineraryService {
  private questions$: Observable<Question[]>;

  constructor(
    private readonly questionsService: QuestionsService,
    private readonly http: HttpClient
  ) {
    // The questions are fetched once and shared among all subscribers.
    this.questions$ = this.questionsService.fetchQuestions().pipe(
      shareReplay(1)
    );
  }

  /**
   * Returns a new answers object with answerTemplate substitutions for each question.
   * @param answers The raw answers map
   * @param questions The array of questions (with answerTemplate)
   */
  mapAnswersWithTemplates(answers: Record<string, any>, questions: Question[]): Record<string, any> {
    // Helper to get display value for a question's answer
    function getDisplayValue(q: Question, val: any): string {
      if (q.type === 'single-select' && q.options) {
        const opt = q.options.find(o => o.value === val);
        return opt?.answerDescription || opt?.label || String(val);
      }
      if (q.type === 'multi-select' && q.options && Array.isArray(val)) {
        return val
          .map(v => {
            const opt = q.options!.find(o => o.value === v);
            return opt?.answerDescription || opt?.label || String(v);
          })
          .join(', ');
      }
      return val !== undefined && val !== null ? String(val) : '';
    }

    // Helper to fill template with answers (using display values)
    function fillTemplate(template: string, ans: Record<string, any>, questions: Question[]): string {
      return template.replace(/\{(.*?)\}/g, (_, key) => {
        const q = questions.find(q => q.id === key);
        if (!q) return ans[key] ?? '';
        return getDisplayValue(q, ans[key]);
      });
    }

    const mapped: Record<string, any> = { ...answers };
    for (const q of questions) {
      if (q.answerTemplate && answers[q.id] !== undefined) {
        mapped[q.id] = fillTemplate(q.answerTemplate, answers, questions);
      }
    }
    return mapped;
  }

  /**
   * It no longer uses a shared Subject, which caused unpredictable behavior.
   * It also waits for the questions to be loaded before constructing the prompt.
   */
  generateViaApi(answers: Record<string, any>): Observable<any> {
    // Use the cached questions$ stream. `switchMap` waits for questions to be
    // available and then switches to the HTTP post observable.
    return this.questions$.pipe(
      switchMap(questions => {
        const promptString = Object.values(this.mapAnswersWithTemplates(answers, questions)).join('\n');
        console.log('Generating itinerary via API with prompt:', promptString);

        const request: PromptRequest = {
          data: {
            answers: answers,
            prompt: promptString,
            history: []
          }
        };

        return this.http.post(
          'https://us-central1-ai-planner-backend-qwerty.cloudfunctions.net/gen_itinerary_chat',
          request
        );
      })
    );
  }
}