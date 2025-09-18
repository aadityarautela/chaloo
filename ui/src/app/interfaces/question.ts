// This interface represents a single question in the questions.json structure

export type QuestionType = 'text' | 'number' | 'single-select' | 'multi-select';

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