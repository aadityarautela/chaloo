import { HttpClient } from '@angular/common/http';
import { Question, QuestionsService } from './questions.service';
import { Injectable } from '@angular/core';
import { debounceTime, Observable, finalize, share, of, Subject, switchMap } from 'rxjs';

export interface PromptRequest {
  data: {
    answers: any;
    prompt: string;
    history: any[];
  }
}

@Injectable({ providedIn: 'root' })
export class ItineraryService {
  /**
   * Returns a new answers object with answerTemplate substitutions for each question.
   * @param answers The raw answers map
   * @param questions The array of questions (with answerTemplate)
   */
    questions: Question[] = [];
      private promptSubject = new Subject<Record<string, any>>();


    constructor(private readonly questionsService: QuestionsService, private readonly http: HttpClient) {
      this.questionsService.fetchQuestions().subscribe((questions) => {
        this.questions = questions;
      });
    }


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

  private currentApiCall: Observable<any> | null = null;
  private readonly DEBOUNCE_TIME = 500; // 500ms debounce

  generateViaApi(answers: Record<string, any>): Observable<any> {
    this.promptSubject.next(answers);
    
    return this.promptSubject.pipe(
      debounceTime(500),
      switchMap(answers => {
        const promptString = Object.values(this.mapAnswersWithTemplates(answers, this.questions)).join('\n');
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
