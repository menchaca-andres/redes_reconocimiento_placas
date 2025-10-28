-- Redes I
-- Reconocimiento de placas:

CREATE TABLE registros_vehiculares (
    id SERIAL PRIMARY KEY,
    placa VARCHAR(20),
    tiene_restriccion INTEGER,  -- 0 = sí, 1 = no
    dia_semana VARCHAR(20),
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    imagen_original BYTEA,
    imagen_placa BYTEA
);

SELECT * FROM registros_vehiculares;

DROP TABLE registros_vehiculares;

CREATE TABLE datos_personales (
	id_dp SERIAL PRIMARY KEY,
	nombres VARCHAR(50),
	apellido_paterno VARCHAR(50),
	apellido_materno VARCHAR(50),
	correo VARCHAR(50),
	placa_reg VARCHAR(10)
);

SELECT * FROM datos_personales;

-- Pones un correo real y dejan esa placa
INSERT INTO datos_personales(nombres, apellido_paterno, apellido_materno, correo, placa_reg) VALUES 
	('Luis Andres', 'Menchaca', 'Rivero', '4mrvro@gmail.com', '5280 YIN'),
	('Yudith', 'Noa', 'Vargas', 'yudith.noa@ucb.edu.bo', '5280 YIN'),
	('Jhamile', 'Llapacu', 'Cruz', 'jhamile.llapacu@ucb.edu.bo', '5280 YIN');

DROP TABLE datos_personales;
