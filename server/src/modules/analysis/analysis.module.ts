import { Module } from '@nestjs/common';
import { AnalysisController } from './analysis.controller';
import { AnalysisService } from './analysis.service';
import { OpenAIService } from './openai.service';

@Module({
  controllers: [AnalysisController],
  providers: [AnalysisService, OpenAIService],
})
export class AnalysisModule {}

