import { Queue, Worker, type Processor } from "bullmq";
import IORedis from "ioredis";

let _connection: IORedis | null = null;

function getConnection() {
  if (!_connection) {
    _connection = new IORedis(process.env.REDIS_URL || "redis://localhost:6379", {
      maxRetriesPerRequest: null,
    });
  }
  return _connection;
}

function getQueue(name: string) {
  return new Queue(name, { connection: getConnection() });
}

export const transcriptionQueue = { add: (name: string, data: unknown) => getQueue("transcription").add(name, data) };
export const alertQueue = { add: (name: string, data: unknown) => getQueue("alert-matching").add(name, data) };
export const summaryQueue = { add: (name: string, data: unknown) => getQueue("summarization").add(name, data) };

export function createWorker<T>(
  queueName: string,
  processor: Processor<T>,
) {
  return new Worker<T>(queueName, processor, {
    connection: getConnection(),
    concurrency: 2,
  });
}

export { getConnection as redisConnection };
