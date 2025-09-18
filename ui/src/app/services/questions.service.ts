import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export type QuestionType = 'text' | 'number' | 'single-select' | 'multi-select' | 'date' | 'date-range';

export interface QuestionOption {
  id: string;
  label: string;
  value: string;
  answerDescription?: string;
}

export interface DateRangeConfig {
  id: string;
  placeholder?: string;
  min?: string; // "today", "start_date + 1", or ISO date string
}

export interface Question {
  id: string;
  type: QuestionType;
  title: string;
  description: string;
  required: boolean;
  answerTemplate: string;
  skipDescription?: string;
  placeholder?: string;
  min?: number;
  max?: number;
  step?: number;
  options?: QuestionOption[];
  maxSelections?: number; // for multi-select
  // For date-range type
  startDate?: DateRangeConfig;
  endDate?: DateRangeConfig;
}

// The full questions.json is an array of Question
export type Questions = Question[];
@Injectable({ providedIn: 'root' })
export class QuestionsService {
  constructor(private readonly http: HttpClient) {}

  fetchQuestions(): Observable<Question[]> {
    return this.http.get<Question[]>('/api/questions.json');
  }
}
