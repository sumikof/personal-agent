"use client";

/**
 * MarkdownContent コンポーネント（FEAT-002）
 *
 * Markdown テキストを HTML にレンダリングする。
 * Redmine チケット URL を新しいタブで開くリンクとして処理する。
 * GFM（GitHub Flavored Markdown）対応: テーブル・太字・箇条書きを正確にレンダリングする。
 */
import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";

interface MarkdownContentProps {
  /** レンダリングする Markdown テキスト */
  content: string;
  /** ストリーミング中かどうか（true のとき最後にカーソルを表示） */
  isStreaming?: boolean;
}

export const MarkdownContent: React.FC<MarkdownContentProps> = ({
  content,
  isStreaming = false,
}) => {
  const components: Components = {
    // リンク: 新しいタブで開く（FEAT-002 の主要要件）
    a: ({ href, children, ...props }) => {
      const isExternal =
        href?.startsWith("http://") || href?.startsWith("https://");
      const isRedmineIssue = href?.includes("/issues/");

      return (
        <a
          href={href}
          target={isExternal ? "_blank" : undefined}
          rel={isExternal ? "noopener noreferrer" : undefined}
          className={[
            "text-blue-600 underline hover:text-blue-800 transition-colors",
            isRedmineIssue ? "font-medium" : "",
          ]
            .filter(Boolean)
            .join(" ")}
          {...props}
        >
          {children}
        </a>
      );
    },

    // 太字: 高優先度タスク（**高** / **🔴 緊急**）のスタイル
    strong: ({ children, ...props }) => (
      <strong className="font-bold text-gray-900" {...props}>
        {children}
      </strong>
    ),

    // 見出し: タスク一覧ヘッダ
    h2: ({ children, ...props }) => (
      <h2
        className="text-base font-semibold text-gray-800 mt-3 mb-2 border-b border-gray-200 pb-1"
        {...props}
      >
        {children}
      </h2>
    ),

    h3: ({ children, ...props }) => (
      <h3 className="text-sm font-semibold text-gray-700 mt-2 mb-1" {...props}>
        {children}
      </h3>
    ),

    // 順序なしリスト
    ul: ({ children, ...props }) => (
      <ul className="list-disc list-inside space-y-1 my-2 text-sm" {...props}>
        {children}
      </ul>
    ),

    // 順序付きリスト: 番号付きタスク一覧（1. 2. 3. ...）
    ol: ({ children, ...props }) => (
      <ol
        className="list-decimal list-inside space-y-1 my-2 text-sm"
        {...props}
      >
        {children}
      </ol>
    ),

    // リスト項目
    li: ({ children, ...props }) => (
      <li className="text-gray-800 leading-relaxed" {...props}>
        {children}
      </li>
    ),

    // 段落
    p: ({ children, ...props }) => (
      <p className="text-sm text-gray-800 leading-relaxed my-1" {...props}>
        {children}
      </p>
    ),

    // コードブロック
    code: ({ children, className, ...props }) => {
      const isBlock = className?.includes("language-");
      if (isBlock) {
        return (
          <code
            className="block bg-gray-100 rounded p-2 text-xs font-mono overflow-x-auto my-2"
            {...props}
          >
            {children}
          </code>
        );
      }
      return (
        <code
          className="bg-gray-100 rounded px-1 text-xs font-mono"
          {...props}
        >
          {children}
        </code>
      );
    },

    // テーブル（GFM）
    table: ({ children, ...props }) => (
      <div className="overflow-x-auto my-2">
        <table className="text-sm border-collapse w-full" {...props}>
          {children}
        </table>
      </div>
    ),

    th: ({ children, ...props }) => (
      <th
        className="border border-gray-300 bg-gray-50 px-3 py-1 text-left font-semibold text-gray-700"
        {...props}
      >
        {children}
      </th>
    ),

    td: ({ children, ...props }) => (
      <td
        className="border border-gray-300 px-3 py-1 text-gray-800"
        {...props}
      >
        {children}
      </td>
    ),
  };

  return (
    <div className="prose prose-sm max-w-none break-words">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
      {isStreaming && (
        <span
          className="inline-block w-2 h-4 bg-gray-400 animate-pulse ml-0.5 align-text-bottom"
          aria-hidden="true"
        />
      )}
    </div>
  );
};
