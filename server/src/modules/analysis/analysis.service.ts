import { Injectable } from '@nestjs/common';
import fetch from 'node-fetch';

@Injectable()
export class AnalysisService {
  private detectionUrl = process.env.DETECTION_URL || 'http://localhost:8001/api/analyze-text';

  async proxyAnalyze(content: string) {
    const res = await fetch(this.detectionUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    });
    if (!res.ok) {
      const text = await res.text();
      return { error: 'detection_error', status: res.status, detail: text.slice(0, 500) };
    }
    return res.json();
  }
}

