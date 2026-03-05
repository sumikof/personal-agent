/**
 * react-markdown のモック（Jest 用）。
 * ESM モジュールのため CJS テスト環境でモックが必要。
 * Markdown テキストをそのまま div にレンダリングする簡易実装。
 */
import React from "react";

interface ReactMarkdownProps {
  children: string;
  remarkPlugins?: unknown[];
  components?: Record<string, React.ComponentType<Record<string, unknown>>>;
}

// シンプルなパーサー: **text** → <strong>, [text](url) → <a>, ## → <h2>
function parseMarkdown(
  text: string,
  components: Record<string, React.ComponentType<Record<string, unknown>>> = {}
): React.ReactNode[] {
  const lines = text.split("\n");
  return lines.map((line, lineIndex) => {
    const key = `line-${lineIndex}`;

    // h2 見出し
    if (line.startsWith("## ")) {
      const H2 = components.h2 as React.FC<Record<string, unknown>> | undefined;
      const content = line.slice(3);
      if (H2) return <H2 key={key}>{content}</H2>;
      return <h2 key={key}>{content}</h2>;
    }

    // h3 見出し
    if (line.startsWith("### ")) {
      const H3 = components.h3 as React.FC<Record<string, unknown>> | undefined;
      const content = line.slice(4);
      if (H3) return <H3 key={key}>{content}</H3>;
      return <h3 key={key}>{content}</h3>;
    }

    // 順序付きリスト
    const olMatch = line.match(/^(\d+)\.\s(.*)/);
    if (olMatch) {
      const Ol = components.ol as React.FC<Record<string, unknown>> | undefined;
      const Li = components.li as React.FC<Record<string, unknown>> | undefined;
      const content = parseInline(olMatch[2], components);
      const liEl = Li ? (
        <Li key={`li-${lineIndex}`}>{content}</Li>
      ) : (
        <li key={`li-${lineIndex}`}>{content}</li>
      );
      if (Ol) return <Ol key={key}>{liEl}</Ol>;
      return <ol key={key}>{liEl}</ol>;
    }

    // 空行
    if (!line.trim()) return <br key={key} />;

    // 通常テキスト（段락）
    const P = components.p as React.FC<Record<string, unknown>> | undefined;
    const content = parseInline(line, components);
    if (P) return <P key={key}>{content}</P>;
    return <p key={key}>{content}</p>;
  });
}

// インライン要素パーサー: **bold**, [text](url)
function parseInline(
  text: string,
  components: Record<string, React.ComponentType<Record<string, unknown>>> = {}
): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  // 正規表現で **bold** と [text](url) を分割
  const regex = /(\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\))/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }

    const token = match[0];
    if (token.startsWith("**")) {
      const boldText = token.slice(2, -2);
      const Strong = components.strong as
        | React.FC<Record<string, unknown>>
        | undefined;
      if (Strong) {
        parts.push(<Strong key={match.index}>{boldText}</Strong>);
      } else {
        parts.push(<strong key={match.index}>{boldText}</strong>);
      }
    } else {
      // [text](url)
      const linkMatch = token.match(/\[([^\]]+)\]\(([^)]+)\)/);
      if (linkMatch) {
        const [, linkText, href] = linkMatch;
        const A = components.a as React.FC<Record<string, unknown>> | undefined;
        if (A) {
          parts.push(
            <A key={match.index} href={href}>
              {linkText}
            </A>
          );
        } else {
          parts.push(
            <a key={match.index} href={href}>
              {linkText}
            </a>
          );
        }
      }
    }

    lastIndex = match.index + token.length;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts;
}

const ReactMarkdown: React.FC<ReactMarkdownProps> = ({
  children,
  components = {},
}) => {
  return (
    <div data-testid="react-markdown">
      {parseMarkdown(children, components)}
    </div>
  );
};

export default ReactMarkdown;
