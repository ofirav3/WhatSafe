import { Injectable, ServiceUnavailableException, InternalServerErrorException } from '@nestjs/common';
import OpenAI from 'openai';

@Injectable()
export class OpenAIService {
  private client: OpenAI | null = null;

  constructor() {
    const key = process.env.OPENAI_API_KEY;
    if (key) {
      this.client = new OpenAI({ apiKey: key });
    }
  }

  async analyzeWithOpenAI(content: string) {
    if (!this.client) {
      throw new ServiceUnavailableException('OpenAI not configured');
    }

    const system =
      'You are an expert analyst detecting boycott activity in WhatsApp group chats. Return only JSON with keys: boycott_detected (bool), confidence (0-1), risk_level (none|low|medium|high), reasoning (string), boycott_details (string), potential_targets (string[]).';

    const user = `Analyze this WhatsApp export:\n\n${content}\n\nReturn only JSON.`;

    try {
      const resp = await this.client.chat.completions.create({
        model: 'gpt-4o-mini',
        temperature: 0.3,
        response_format: { type: 'json_object' },
        messages: [
          { role: 'system', content: system },
          { role: 'user', content: user },
        ],
      });

      const parsed = JSON.parse(resp.choices[0].message.content ?? '{}');
      return {
        source: 'openai-ai-analysis',
        label: (parsed.risk_level ?? 'unknown').toUpperCase() + ' risk',
        boycott_detected: parsed.boycott_detected ?? false,
        confidence: parsed.confidence ?? 0,
        risk_level: parsed.risk_level ?? 'none',
        reasoning: parsed.reasoning ?? '',
        boycott_details: parsed.boycott_details ?? '',
        potential_targets: parsed.potential_targets ?? [],
        model_used: 'gpt-4o-mini',
      };
    } catch (err: any) {
      const reason = err?.message || 'OpenAI call failed';
      throw new InternalServerErrorException(`OpenAI error: ${reason}`);
    }
  }
}

