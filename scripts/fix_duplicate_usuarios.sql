-- Fix duplicate usuarios by telefono
-- Keep the oldest user for each phone number and migrate data

BEGIN;

-- 1. Identify duplicates and their relationships
-- Phone: +573001234567 (Admin vs Cliente)
--    Keep: 38d8ccff-c9e4-4d92-8858-05c4039c5c06 (Admin - oldest)
--    Remove: 4aab0153-95e1-4f84-b454-fd45c6069675 (Cliente)

-- Phone: +573006515619 (Cliente vs Asesor)
--    Keep: 8c811dd9-3f22-4da4-baa9-2bbd605ccb1e (Cliente - oldest)
--    Remove: fe40ba8d-a694-40e2-a8fa-7916e763613c (Asesor)

-- 2. Migrate clientes data from duplicate to keep
-- For +573001234567: Migrate cliente profile to admin user
UPDATE clientes 
SET usuario_id = '38d8ccff-c9e4-4d92-8858-05c4039c5c06'
WHERE usuario_id = '4aab0153-95e1-4f84-b454-fd45c6069675';

-- For +573006515619: Keep cliente, migrate asesor data
-- First check if there's an asesor profile to migrate
UPDATE asesores 
SET usuario_id = '8c811dd9-3f22-4da4-baa9-2bbd605ccb1e'
WHERE usuario_id = 'fe40ba8d-a694-40e2-a8fa-7916e763613c';

-- 3. Migrate any solicitudes relationships
UPDATE solicitudes 
SET cliente_id = (SELECT id FROM clientes WHERE usuario_id = '38d8ccff-c9e4-4d92-8858-05c4039c5c06')
WHERE cliente_id IN (SELECT id FROM clientes WHERE usuario_id = '4aab0153-95e1-4f84-b454-fd45c6069675');

UPDATE solicitudes 
SET cliente_id = (SELECT id FROM clientes WHERE usuario_id = '8c811dd9-3f22-4da4-baa9-2bbd605ccb1e')
WHERE cliente_id IN (SELECT id FROM clientes WHERE usuario_id = 'fe40ba8d-a694-40e2-a8fa-7916e763613c');

-- 4. Migrate ofertas relationships
UPDATE ofertas 
SET asesor_id = (SELECT id FROM asesores WHERE usuario_id = '8c811dd9-3f22-4da4-baa9-2bbd605ccb1e')
WHERE asesor_id IN (SELECT id FROM asesores WHERE usuario_id = 'fe40ba8d-a694-40e2-a8fa-7916e763613c');

-- 5. Skip evaluaciones migration (no asesor_id column)

-- 6. Delete orphaned cliente/asesor profiles
DELETE FROM clientes WHERE usuario_id = '4aab0153-95e1-4f84-b454-fd45c6069675';
DELETE FROM asesores WHERE usuario_id = 'fe40ba8d-a694-40e2-a8fa-7916e763613c';

-- 7. Delete duplicate usuarios
DELETE FROM usuarios WHERE id = '4aab0153-95e1-4f84-b454-fd45c6069675';
DELETE FROM usuarios WHERE id = 'fe40ba8d-a694-40e2-a8fa-7916e763613c';

-- 8. Add UNIQUE constraint to prevent future duplicates
ALTER TABLE usuarios ADD CONSTRAINT usuarios_telefono_unique UNIQUE (telefono);

-- 9. Verify results
SELECT 'Remaining usuarios with these phones:' as status;
SELECT id, email, nombre, apellido, telefono, rol 
FROM usuarios 
WHERE telefono IN ('+573001234567', '+573006515619')
ORDER BY telefono;

SELECT 'Total usuarios count:' as status;
SELECT COUNT(*) as total FROM usuarios;

COMMIT;
