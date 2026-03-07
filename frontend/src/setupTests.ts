/**
 * Jest テスト環境のセットアップ。
 * jsdom 環境で不足している Web API のポリフィルを提供する。
 */
import "@testing-library/jest-dom";

// jsdom は Node の globalThis を上書きするため、Node モジュールから直接ポリフィルする
// eslint-disable-next-line @typescript-eslint/no-require-imports
const { ReadableStream } = require("stream/web") as typeof import("stream/web");
// @ts-expect-error
global.ReadableStream = ReadableStream;

if (typeof global.TextEncoder === "undefined") {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { TextEncoder, TextDecoder } = require("util") as typeof import("util");
  // @ts-expect-error
  global.TextEncoder = TextEncoder;
  // @ts-expect-error
  global.TextDecoder = TextDecoder;
}

// crypto.randomUUID のポリフィル（jsdom は crypto を提供するが randomUUID が未定義）
if (typeof (global.crypto as Crypto | undefined)?.randomUUID === "undefined") {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const nodeCrypto = require("crypto") as typeof import("crypto");
  // @ts-expect-error - randomUUID を既存の crypto オブジェクトに追加
  global.crypto.randomUUID = () => nodeCrypto.randomUUID();
}
