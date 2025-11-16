import 'reflect-metadata';
import * as dotenv from 'dotenv';
import { join } from 'path';
// Load env from current working directory (npm run start:dev) and built dist folder fallback
dotenv.config(); // loads from process.cwd()/.env
dotenv.config({ path: join(__dirname, '..', '..', '.env') }); // loads from server/.env after build

import { NestFactory } from '@nestjs/core';
import { AppModule } from './modules/app.module';
import { ValidationPipe } from '@nestjs/common';
import { json, urlencoded } from 'express';

async function bootstrap() {
  const app = await NestFactory.create(AppModule, { cors: { origin: ['http://localhost:5173', 'http://127.0.0.1:5173'] } });
  // Increase body size limits to handle larger WhatsApp exports
  app.use(json({ limit: '5mb' }));
  app.use(urlencoded({ extended: true, limit: '5mb' }));
  app.setGlobalPrefix('api');
  app.useGlobalPipes(new ValidationPipe({ whitelist: true, transform: true }));

  const port = process.env.PORT ? parseInt(process.env.PORT, 10) : 3000;
  await app.listen(port);
  // eslint-disable-next-line no-console
  console.log(`WhatSafe Nest server listening on http://localhost:${port}`);
  if (!process.env.OPENAI_API_KEY) {
    console.warn('OPENAI_API_KEY not set - /api/analyze-text-ai will return 503');
  }
}
bootstrap();

