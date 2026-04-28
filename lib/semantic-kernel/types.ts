/**
 * Shared types mirroring the Microsoft Semantic Kernel TypeScript SDK API.
 */

export interface ChatMessageContent {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface StreamingChatMessageContent {
  content: string;
  role?: string;
}

export interface KernelArguments {
  [key: string]: unknown;
}

export interface AzureOpenAIConfig {
  deploymentName: string;
  endpoint: string;
  apiKey: string;
  apiVersion?: string;
}

export interface CompletionOptions {
  /** JSON mode — Orchestrator uses this for structured output */
  responseFormat?: 'json_object' | 'text';
  temperature?: number;
  maxTokens?: number;
}
