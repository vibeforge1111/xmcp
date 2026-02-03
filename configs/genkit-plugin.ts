/**
 * Firebase Genkit MCP Plugin Configuration
 *
 * Install: npm install genkitx-mcp
 *
 * Usage in your Genkit app:
 */

import { genkit } from 'genkit';
import { mcpClient } from 'genkitx-mcp';

// Initialize Genkit with X-Twitter MCP
const ai = genkit({
  plugins: [
    mcpClient({
      name: 'x-twitter',
      serverProcess: {
        command: 'x-twitter-mcp-server',
        env: {
          TWITTER_API_KEY: process.env.TWITTER_API_KEY!,
          TWITTER_API_SECRET: process.env.TWITTER_API_SECRET!,
          TWITTER_ACCESS_TOKEN: process.env.TWITTER_ACCESS_TOKEN!,
          TWITTER_ACCESS_TOKEN_SECRET: process.env.TWITTER_ACCESS_TOKEN_SECRET!,
          TWITTER_BEARER_TOKEN: process.env.TWITTER_BEARER_TOKEN!,
          X_MCP_PROFILE: 'researcher',
        },
      },
    }),
  ],
});

// Example: Use X-Twitter tools in a flow
export const searchTwitterFlow = ai.defineFlow(
  {
    name: 'searchTwitter',
    inputSchema: { type: 'object', properties: { query: { type: 'string' } } },
  },
  async (input) => {
    const result = await ai.runTool('search_twitter', {
      query: input.query,
      count: 10,
      product: 'Top',
    });
    return result;
  }
);

// Example: Fetch X article
export const fetchArticleFlow = ai.defineFlow(
  {
    name: 'fetchXArticle',
    inputSchema: { type: 'object', properties: { url: { type: 'string' } } },
  },
  async (input) => {
    // IMPORTANT: Use get_article, not WebFetch - X articles need Playwright
    const result = await ai.runTool('get_article', {
      url: input.url,
    });
    return result;
  }
);
