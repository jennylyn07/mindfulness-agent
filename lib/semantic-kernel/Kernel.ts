import OpenAI from 'openai';
import type { AzureOpenAIConfig } from './types';

/**
 * Kernel — mirrors Microsoft Semantic Kernel's Kernel class.
 * Holds the underlying Azure OpenAI client shared across all agents.
 * Built via the static builder() pattern matching SK's fluent API.
 *
 * SK equivalent:
 *   const kernel = Kernel.builder()
 *     .addAzureOpenAIChatCompletion(deployment, endpoint, key)
 *     .build();
 */
export class Kernel {
  readonly openai: OpenAI;
  readonly config: AzureOpenAIConfig;

  private constructor(config: AzureOpenAIConfig, openai: OpenAI) {
    this.config = config;
    this.openai = openai;
  }

  static builder(): KernelBuilder {
    return new KernelBuilder();
  }
}

class KernelBuilder {
  private _config: Partial<AzureOpenAIConfig> = {};

  addAzureOpenAIChatCompletion(
    deploymentName: string,
    endpoint: string,
    apiKey: string,
    apiVersion = '2024-02-01'
  ): this {
    this._config = { deploymentName, endpoint, apiKey, apiVersion };
    return this;
  }

  build(): Kernel {
    const { deploymentName, endpoint, apiKey, apiVersion } = this._config as AzureOpenAIConfig;

    if (!deploymentName || !endpoint || !apiKey) {
      throw new Error(
        '[Kernel] Missing Azure OpenAI config. Call addAzureOpenAIChatCompletion() before build().'
      );
    }

    const openai = new OpenAI({
      apiKey,
      baseURL: `${endpoint}openai/deployments/${deploymentName}`,
      defaultQuery: { 'api-version': apiVersion ?? '2024-02-01' },
      defaultHeaders: { 'api-key': apiKey },
    });

    return new (Kernel as any)({ deploymentName, endpoint, apiKey, apiVersion }, openai);
  }
}
