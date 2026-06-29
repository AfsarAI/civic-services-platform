/* eslint-env node */
module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
    node: true,
  },
  extends: [
    'eslint:recommended',
    // vue3-essential: correctness rules only, no formatting/style rules
    'plugin:vue/vue3-essential',
  ],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  rules: {
    // Scaffold: stub functions intentionally have unused params / imports
    'no-unused-vars': 'off',
    'vue/multi-word-component-names': 'off',
    'vue/no-v-html': 'off',
  },
};
