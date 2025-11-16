import { IsString, MinLength } from 'class-validator';

export class AnalyzeDto {
  @IsString()
  @MinLength(1)
  content!: string;
}

