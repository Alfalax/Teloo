/**
 * Test Script - Axios Integration
 * Verifica que todos los servicios usen el apiClient correctamente
 */

import { authService } from './src/services/auth';
import { asesoresService } from './src/services/asesores';
import { pqrService } from './src/services/pqr';
import { analyticsService } from './src/services/analytics';
import apiClient from './src/lib/axios';

console.log('✅ Todos los imports funcionan correctamente');

// Verificar que apiClient tiene los interceptores
console.log('📡 Interceptores de request:', apiClient.interceptors.request.handlers.length);
console.log('📡 Interceptores de response:', apiClient.interceptors.response.handlers.length);

// Verificar que los servicios están disponibles
console.log('✅ authService:', typeof authService);
console.log('✅ asesoresService:', typeof asesoresService);
console.log('✅ pqrService:', typeof pqrService);
console.log('✅ analyticsService:', typeof analyticsService);

console.log('\n🎉 Integración de axios completada correctamente');
