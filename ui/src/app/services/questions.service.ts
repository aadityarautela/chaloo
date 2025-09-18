import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export type QuestionType = 'text' | 'number' | 'single-select' | 'multi-select' | "date";

export interface QuestionOption {
  id: string;
  label: string;
  value: string;
  answerDescription?: string;
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
