// stores/index.ts
import { createPinia } from 'pinia';

const pinia = createPinia();

export default pinia;

export * from './auth';
export * from './devices';
export * from './sensors';
export * from './alarms';
export * from './dashboard';
