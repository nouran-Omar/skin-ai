export type QuestionType = "single" | "multi" | "number" | "scale";
export interface Option { value: string; label: string; exclusive?: boolean; hint?: string }
export interface ShowIf { question: string; equals?: string; includes?: string; includes_any?: string[]; in?: string[] }
export interface Question {
  id: string; type: QuestionType; text: string; section: string; help?: string; required?: boolean;
  options?: Option[]; min?: number; max?: number; unit?: string; show_if?: ShowIf;
}
export type AnswerValue = string | string[] | number;
export type Answers = Record<string, AnswerValue>;

export interface Prediction {
  label: string; name: string; risk: string; description: string; probability: number; adjusted_probability: number;
}
export interface Urgency { level: "urgent" | "soon" | "routine"; title: string; message: string }
export interface AnalysisResult {
  id: string; created_at: string; demo: boolean;
  model: { arch: string; classes: number; test_macro_f1: number | null; temperature: number };
  predictions: Prediction[]; urgency: Urgency;
  context_factors: { reason: string; effects: Record<string, number> }[];
  warnings: string[];
  preprocessing: { original_size: string; model_input_size: string; steps: string[]; hair_coverage_pct: number; sharpness_score: number; mean_brightness: number; normalisation: string };
  answers_summary: { question: string; answer: string }[];
  images: { processed: string; gradcam: string };
  disclaimer: string;
}
