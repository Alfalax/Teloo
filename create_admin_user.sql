-- Create admin user for TeLOO V3
INSERT INTO usuarios (
    id, 
    email, 
    password_hash, 
    nombre, 
    apellido, 
    telefono, 
    rol, 
    estado,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    'admin@teloo.com',
    '$2b$12$I0Zqba39D8vzajeVGpdTJOiy/S.93rws5GNsT7rlmZ1S/ZpaN2D3u',
    'Administrador',
    'TeLOO',
    '+573001234567',
    'ADMIN',
    'ACTIVO',
    NOW(),
    NOW()
);