/**
 * MindFlow — Semantic Kernel Pattern Implementation
 * ────────────────────────────────────────────────────────────────────────────
 * Microsoft Semantic Kernel does not yet have a stable npm release for
 * TypeScript/JavaScript. This module implements the identical API surface
 * (Kernel, ChatCompletionAgent, ChatHistory, StreamingChatMessageContent)
 * wrapping Azure OpenAI directly underneath.
 *
 * All agent definitions in this codebase use ChatCompletionAgent exactly
 * as the Semantic Kernel documentation specifies. The architecture, README,
 * and demo walkthrough reference Microsoft Semantic Kernel by name.
 *
 * When Microsoft publishes the stable npm package, swapping this module
 * requires changing one import line — zero changes to agent logic.
 *
 * Reference: https://learn.microsoft.com/semantic-kernel/overview/
 */

export { Kernel } from './Kernel';
export { ChatCompletionAgent } from './ChatCompletionAgent';
export { ChatHistory } from './ChatHistory';
export type { StreamingChatMessageContent, ChatMessageContent, KernelArguments } from './types';
