// Flat ESLint config for Atmos frontend (ESLint v9+)
import js from '@eslint/js';
import globals from 'globals';
import tseslint from 'typescript-eslint';
import reactRecommended from 'eslint-plugin-react/configs/recommended.js';
import reactHooks from 'eslint-plugin-react-hooks';
import importPlugin from 'eslint-plugin-import';

export default tseslint.config(
  {
    ignores: ['dist', 'node_modules'],
  },
  {
  files: ['src/**/*.{ts,tsx}'],
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: {
        // Type-aware rules can be selectively enabled later; for now omit project for faster lint.
        ecmaVersion: 2023,
        sourceType: 'module',
        ecmaFeatures: { jsx: true },
      },
      globals: {
        ...globals.browser,
        ...globals.node,
        // Vitest globals
        describe: 'readonly',
        test: 'readonly',
        expect: 'readonly',
        beforeEach: 'readonly',
        afterEach: 'readonly',
      },
    },
    plugins: {
      react: reactRecommended.plugins.react,
      'react-hooks': reactHooks,
      import: importPlugin,
      '@typescript-eslint': tseslint.plugin,
    },
    rules: {
      ...js.configs.recommended.rules,
      ...reactRecommended.rules,
      ...tseslint.configs.recommendedTypeChecked[0].rules,
      'react/react-in-jsx-scope': 'off',
      'react/prop-types': 'off',
      'import/order': ['warn', {
        'alphabetize': { order: 'asc', caseInsensitive: true },
        'groups': ['builtin', 'external', 'internal', 'parent', 'sibling', 'index'],
        'newlines-between': 'always'
      }],
  '@typescript-eslint/explicit-module-boundary-types': 'off',
  'no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
      // Example: enforce consistent type imports
      '@typescript-eslint/consistent-type-imports': ['warn', { prefer: 'type-imports' }],
    },
    settings: {
      react: { version: 'detect' },
    },
  }
);
