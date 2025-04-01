USE disc_golf_db;

CREATE TABLE product_table (
    unique_id VARCHAR(256),
    title VARCHAR(255),
    price DECIMAL(10, 2),
    currency VARCHAR(5),
    speed DECIMAL(3, 1),
    glide DECIMAL(3, 1),
    turn DECIMAL(3, 1),
    fade DECIMAL(3, 1),
    link_to_disc VARCHAR(255),
    image_url VARCHAR(255),
    store VARCHAR(255),
    PRIMARY KEY (unique_id)
);

CREATE TABLE users (
    id VARCHAR(255),
    e_mail VARCHAR(255),
    picture_url VARCHAR(255),
    product_history JSON,
    PRIMARY KEY (id)
);