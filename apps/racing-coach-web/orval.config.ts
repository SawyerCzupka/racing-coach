import { defineConfig } from 'orval';

export default defineConfig({
  racingCoach: {
    input: {
      target: 'http://localhost:8000/openapi.json',
    },
    output: {
      mode: 'tags-split',
      target: 'src/api/generated',
      schemas: 'src/api/generated/models',
      client: 'react-query',
      httpClient: 'fetch',
      override: {
        mutator: {
          path: './src/api/client.ts',
          name: 'customFetch',
        },
        query: {
          useQuery: true,
          useSuspenseQuery: false,
        },
      },
    },
    hooks: {
      afterAllFilesWrite: 'prettier --write',
    },
  },
});
