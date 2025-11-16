import { Body, Controller, Post } from '@nestjs/common';
import { AnalysisService } from './analysis.service';
import { AnalyzeDto } from './dto/analyze.dto';
import { OpenAIService } from './openai.service';

@Controller()
export class AnalysisController {
  constructor(private readonly analysis: AnalysisService, private readonly openai: OpenAIService) {}

  @Post('analyze-text')
  async analyzeText(@Body() body: AnalyzeDto) {
    return this.analysis.proxyAnalyze(body.content);
  }

  @Post('analyze-text-ai')
  async analyzeTextAI(@Body() body: AnalyzeDto) {
    return this.openai.analyzeWithOpenAI(body.content);
  }
}

