/** @type {import('jest').Config} */
const config = {
  testEnvironment: "jsdom",
  transform: {
    "^.+\\.(ts|tsx)$": [
      "ts-jest",
      {
        tsconfig: {
          jsx: "react-jsx",
          esModuleInterop: true,
          paths: {
            "@/*": ["./src/*"],
          },
        },
      },
    ],
  },
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
    // ESM モジュールを CJS モックに置き換える
    "^react-markdown$": "<rootDir>/src/__mocks__/react-markdown.tsx",
    "^remark-gfm$": "<rootDir>/src/__mocks__/remark-gfm.ts",
  },
  testMatch: ["**/__tests__/**/*.test.(ts|tsx)"],
  setupFilesAfterEnv: ["<rootDir>/src/setupTests.ts"],
};

module.exports = config;
