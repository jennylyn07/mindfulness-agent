import type { ChatMessageContent } from './types';

/**
 * ChatHistory — mirrors Microsoft Semantic Kernel's ChatHistory class.
 * Holds the ordered list of messages for a conversation turn.
 *
 * SK equivalent:
 *   const history = new ChatHistory();
 *   history.addUserMessage("I'm feeling anxious");
 */
export class ChatHistory {
  readonly messages: ChatMessageContent[] = [];

  addUserMessage(content: string): void {
    this.messages.push({ role: 'user', content });
  }

  addAssistantMessage(content: string): void {
    this.messages.push({ role: 'assistant', content });
  }

  addSystemMessage(content: string): void {
    this.messages.push({ role: 'system', content });
  }

  /** Build from prior conversation turns (for multi-turn context) */
  static fromMessages(messages: ChatMessageContent[]): ChatHistory {
    const history = new ChatHistory();
    for (const m of messages) {
      history.messages.push(m);
    }
    return history;
  }
}
