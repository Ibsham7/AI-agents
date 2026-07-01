import { Topic, Doc, QuizData, ChatMessage } from "../types";

export const TOPICS: Topic[] = [
  { name: "Machine Learning", accuracy: 87, timesQuizzed: 12, needsReview: false, color: "#4f7296" },
  { name: "Linear Algebra", accuracy: 62, timesQuizzed: 8, needsReview: true, color: "#d97706" },
  { name: "Calculus", accuracy: 94, timesQuizzed: 20, needsReview: false, color: "#16a34a" },
  { name: "Data Structures", accuracy: 45, timesQuizzed: 6, needsReview: true, color: "#dc2626" },
  { name: "Statistics", accuracy: 78, timesQuizzed: 15, needsReview: false, color: "#0891b2" },
  { name: "Python", accuracy: 91, timesQuizzed: 18, needsReview: false, color: "#9333ea" },
];

export const RADAR_LABELS: Record<string, string> = {
  "Machine Learning": "ML",
  "Linear Algebra": "Lin. Alg.",
  "Calculus": "Calculus",
  "Data Structures": "Data Str.",
  "Statistics": "Stats",
  "Python": "Python",
};

export const RADAR_DATA = TOPICS.map((t) => ({
  subject: RADAR_LABELS[t.name] ?? t.name,
  score: t.accuracy,
  fullMark: 100,
}));

export const DOCS: Doc[] = [
  { id: 1, name: "ML_Fundamentals.pdf", date: "Jun 28, 2026", status: "ready", size: "4.2 MB" },
  { id: 2, name: "Linear_Algebra_Notes.pdf", date: "Jun 30, 2026", status: "ready", size: "2.8 MB" },
  { id: 3, name: "Calculus_Derivatives.pdf", date: "Jul 1, 2026", status: "processing", size: "6.1 MB" },
];

export const QUIZ: QuizData = {
  question: "What happens when the learning rate in gradient descent is set too high?",
  options: [
    "The model converges faster and more accurately",
    "The model may overshoot the minimum and fail to converge",
    "Training becomes extremely slow but always converges",
    "Gradient updates become zero and training stops",
  ],
  correctIndex: 1,
  explanation:
    "A learning rate that's too high causes large parameter updates that overshoot the loss minimum. This leads to oscillation or divergence — the loss may actually increase rather than decrease over time.",
};

export const INITIAL_MESSAGES: ChatMessage[] = [
  {
    id: 1,
    role: "ai",
    time: "2:14 PM",
    content:
      "Hi Alex! I've reviewed **ML_Fundamentals.pdf**. I'm ready to help you master these concepts. What would you like to explore?\n\n- Supervised vs. Unsupervised Learning\n- Neural Network Architectures\n- Model Evaluation Metrics\n- Gradient Descent & Optimization",
  },
  {
    id: 2,
    role: "user",
    time: "2:15 PM",
    content: "Can you explain gradient descent to me?",
  },
  {
    id: 3,
    role: "ai",
    time: "2:15 PM",
    content:
      "Gradient descent is an optimization algorithm that minimizes a loss function by iteratively moving in the direction of steepest descent.\n\n**Key steps:**\n- Initialize parameters randomly\n- Compute the gradient of the loss ∇L(θ)\n- Update: θ = θ − α∇L(θ)\n- Repeat until convergence\n\nThe **learning rate (α)** controls step size — too high and you overshoot, too low and training crawls. Ready for a quick quiz to test your understanding?",
  },
  {
    id: 4,
    role: "user",
    time: "2:17 PM",
    content: "Yes, quiz me!",
  },
  {
    id: 5,
    role: "quiz",
    time: "2:17 PM",
    quiz: QUIZ,
  },
];
