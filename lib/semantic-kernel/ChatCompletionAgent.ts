import type { Kernel } from './Kernel';
import type { ChatHistory } from './ChatHistory';
import type { StreamingChatMessageContent, CompletionOptions } from './types';

interface ChatCompletionAgentOptions {
  kernel: Kernel;
  /** Agent name — shown in agent badges (e.g. "Sage", "River", "Grove", "Lumen") */
  name: string;
  /** System prompt — inject {memoryContext} before passing */
  instructions: string;
}

/**
 * ChatCompletionAgent — mirrors Microsoft Semantic Kernel's ChatCompletionAgent.
 * Each specialist agent (Sage, River, Grove, Lumen) and the Orchestrator
 * is instantiated as a ChatCompletionAgent with its own instructions.
 *
 * SK equivalent:
 *   const agent = new ChatCompletionAgent({ kernel, name: "Sage", instructions: PROMPT });
 *   for await (const chunk of agent.invokeStreaming(history)) { ... }
 */
export class ChatCompletionAgent {
  readonly name: string;
  private readonly kernel: Kernel;
  private readonly instructions: string;

  constructor({ kernel, name, instructions }: ChatCompletionAgentOptions) {
    this.kernel = kernel;
    this.name = name;
    this.instructions = instructions;
  }

  /**
   * invoke() — non-streaming completion (used by Orchestrator for JSON mode).
   * Returns the full response string.
   */
  async invoke(
    history: ChatHistory,
    options: CompletionOptions = {}
  ): Promise<string> {
    const messages = this._buildMessages(history);

    const response = await this.kernel.openai.chat.completions.create({
      model: this.kernel.config.deploymentName,
      messages,
      temperature: options.temperature ?? 0,
      max_tokens: options.maxTokens ?? 512,
      response_format:
        options.responseFormat === 'json_object'
          ? { type: 'json_object' }
          : { type: 'text' },
    });

    return response.choices[0]?.message?.content ?? '';
  }

  /**
   * invokeStreaming() — streaming completion (used by all specialist agents).
   * Yields StreamingChatMessageContent chunks for SSE piping.
   *
   * Usage:
   *   for await (const chunk of agent.invokeStreaming(history)) {
   *     controller.enqueue(encoder.encode(chunk.content));
   *   }
   */
  async *invokeStreaming(
    history: ChatHistory,
    options: CompletionOptions = {}
  ): AsyncGenerator<StreamingChatMessageContent> {
    const messages = this._buildMessages(history);

    const stream = await this.kernel.openai.chat.completions.create({
      model: this.kernel.config.deploymentName,
      messages,
      temperature: options.temperature ?? 0.7,
      max_tokens: options.maxTokens ?? 1024,
      stream: true,
    });

    for await (const chunk of stream) {
      const content = chunk.choices[0]?.delta?.content;
      if (content) {
        yield { content, role: 'assistant' };
      }
    }
  }

  private _buildMessages(
    history: ChatHistory
  ): Array<{ role: 'system' | 'user' | 'assistant'; content: string }> {
    return [
      { role: 'system', content: this.instructions },
      ...history.messages.map((m) => ({
        role: m.role as 'user' | 'assistant',
        content: m.content,
      })),
    ];
  }
}
